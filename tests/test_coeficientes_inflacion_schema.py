import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tablas_coeficientes_inflacion():
    """Valida columnas base para indices y coeficientes de inflacion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        columnas_indices = {
            row["name"]
            for row in get_db().execute(
                "PRAGMA table_info(indices_inflacion)"
            ).fetchall()
        }
        columnas_coeficientes = {
            row["name"]
            for row in get_db().execute(
                "PRAGMA table_info(ejercicios_coeficientes_inflacion)"
            ).fetchall()
        }

    assert {
        "id",
        "periodo_yyyymm",
        "indice_10000",
        "creado_en",
        "actualizado_en",
    }.issubset(columnas_indices)

    assert {
        "id",
        "ejercicio_id",
        "periodo_yyyymm",
        "indice_inicio_10000",
        "indice_cierre_periodo_yyyymm",
        "indice_cierre_10000",
        "coeficiente_1000000000000",
        "calculado_en",
    }.issubset(columnas_coeficientes)


def test_indices_inflacion_rechaza_periodo_invalido():
    """Valida que el periodo de indice respete formato YYYYMM mensual."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO indices_inflacion (
                    periodo_yyyymm,
                    indice_10000
                )
                VALUES (?, ?)
                """,
                (202613, 74914514),
            )


def test_indices_inflacion_rechaza_indice_no_positivo():
    """Valida que los indices se guarden como enteros positivos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO indices_inflacion (
                    periodo_yyyymm,
                    indice_10000
                )
                VALUES (?, ?)
                """,
                (202501, 0),
            )


def test_indices_inflacion_periodo_es_unico():
    """Valida que exista un unico indice cargado por periodo mensual."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
            """
            INSERT INTO indices_inflacion (
                periodo_yyyymm,
                indice_10000
            )
            VALUES (?, ?)
            """,
            (202501, 78641257),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO indices_inflacion (
                    periodo_yyyymm,
                    indice_10000
                )
                VALUES (?, ?)
                """,
                (202501, 78641258),
            )


def test_coeficientes_inflacion_requiere_ejercicio_existente():
    """Valida integridad entre coeficientes y ejercicios contables."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO ejercicios_coeficientes_inflacion (
                    ejercicio_id,
                    periodo_yyyymm,
                    indice_inicio_10000,
                    indice_cierre_periodo_yyyymm,
                    indice_cierre_10000,
                    coeficiente_1000000000000
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    999,
                    202501,
                    78641257,
                    202512,
                    101213715,
                    1287030737568,
                ),
            )


def test_coeficientes_inflacion_periodo_es_unico_por_ejercicio():
    """Valida que cada ejercicio tenga una sola fila por periodo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        ejercicio_id = _crear_ejercicio_contable(db)

        db.execute(
            """
            INSERT INTO ejercicios_coeficientes_inflacion (
                ejercicio_id,
                periodo_yyyymm,
                indice_inicio_10000,
                indice_cierre_periodo_yyyymm,
                indice_cierre_10000,
                coeficiente_1000000000000
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ejercicio_id,
                202501,
                78641257,
                202512,
                101213715,
                1287030737568,
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ejercicios_coeficientes_inflacion (
                    ejercicio_id,
                    periodo_yyyymm,
                    indice_inicio_10000,
                    indice_cierre_periodo_yyyymm,
                    indice_cierre_10000,
                    coeficiente_1000000000000
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ejercicio_id,
                    202501,
                    78641257,
                    202512,
                    101213715,
                    1287030737568,
                ),
            )


def test_coeficientes_inflacion_cascade_al_borrar_ejercicio():
    """Valida que los coeficientes se borren junto con su ejercicio contable."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        ejercicio_id = _crear_ejercicio_contable(db)

        db.execute(
            """
            INSERT INTO ejercicios_coeficientes_inflacion (
                ejercicio_id,
                periodo_yyyymm,
                indice_inicio_10000,
                indice_cierre_periodo_yyyymm,
                indice_cierre_10000,
                coeficiente_1000000000000
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ejercicio_id,
                202501,
                78641257,
                202512,
                101213715,
                1287030737568,
            ),
        )

        db.execute(
            "DELETE FROM ejercicios_contables WHERE id = ?",
            (ejercicio_id,),
        )

        fila = db.execute(
            """
            SELECT id
            FROM ejercicios_coeficientes_inflacion
            WHERE ejercicio_id = ?
            """,
            (ejercicio_id,),
        ).fetchone()

    assert fila is None


def _crear_ejercicio_contable(db):
    cursor = db.execute(
        """
        INSERT INTO ejercicios_contables (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            fase_cierre,
            bloqueado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "EJ2025",
            "Ejercicio 2025",
            "2025-01-01",
            "2025-12-31",
            "ABIERTO",
            1,
            "ABIERTO",
            0,
        ),
    )

    return cursor.lastrowid
