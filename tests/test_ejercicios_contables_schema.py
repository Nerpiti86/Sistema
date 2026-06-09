import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tabla_ejercicios_contables():
    """Valida el contrato base de columnas de ejercicios_contables."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute(
            "PRAGMA table_info(ejercicios_contables)"
        ).fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "codigo",
        "nombre",
        "fecha_desde",
        "fecha_hasta",
        "estado",
        "activo",
        "creado_en",
        "actualizado_en",
        "fase_cierre",
        "bloqueado",
        "bloqueado_en",
        "observaciones_cierre",
        "es_primer_ejercicio",
    }.issubset(column_names)


def test_ejercicios_contables_permite_un_solo_activo():
    """Valida que la base impida mas de un ejercicio activo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
            """
            INSERT INTO ejercicios_contables (
                codigo,
                nombre,
                fecha_desde,
                fecha_hasta,
                estado,
                activo
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "EJ2026",
                "Ejercicio 2026",
                "2026-01-01",
                "2026-12-31",
                "ABIERTO",
                1,
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ejercicios_contables (
                    codigo,
                    nombre,
                    fecha_desde,
                    fecha_hasta,
                    estado,
                    activo
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "EJ2027",
                    "Ejercicio 2027",
                    "2027-01-01",
                    "2027-12-31",
                    "ABIERTO",
                    1,
                ),
            )


def test_ejercicios_contables_rechaza_rango_invalido():
    """Valida que fecha_hasta no pueda ser menor que fecha_desde."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ejercicios_contables (
                    codigo,
                    nombre,
                    fecha_desde,
                    fecha_hasta
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "EJ_MAL",
                    "Ejercicio invalido",
                    "2026-12-31",
                    "2026-01-01",
                ),
            )


def test_ejercicios_contables_rechaza_estado_invalido():
    """Valida estados contables cerrados a contrato."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ejercicios_contables (
                    codigo,
                    nombre,
                    fecha_desde,
                    fecha_hasta,
                    estado
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "EJ_ESTADO_MAL",
                    "Ejercicio estado invalido",
                    "2026-01-01",
                    "2026-12-31",
                    "BORRADOR",
                ),
            )


def test_ejercicios_contables_define_condicion_operable():
    """Valida la condicion minima para permitir operaciones futuras."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
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
                "EJ2026",
                "Ejercicio 2026",
                "2026-01-01",
                "2026-12-31",
                "ABIERTO",
                1,
                "ABIERTO",
                0,
            ),
        )

        row = db.execute(
            """
            SELECT codigo
            FROM ejercicios_contables
            WHERE codigo = ?
              AND estado = 'ABIERTO'
              AND fase_cierre IN ('ABIERTO', 'EN_CIERRE')
              AND bloqueado = 0
            """,
            ("EJ2026",),
        ).fetchone()

    assert row is not None
    assert row["codigo"] == "EJ2026"
