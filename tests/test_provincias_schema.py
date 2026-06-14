import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.paises_repository import crear_pais


def _crear_pais(nombre="Argentina", codigo_iso="AR"):
    return crear_pais(
        {
            "nombre": nombre,
            "codigo_iso": codigo_iso,
            "activo": 1,
            "orden": 10,
        }
    )


def test_migracion_crea_tabla_provincias():
    """Valida columnas base del maestro comun de provincias."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA table_info(provincias)").fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "pais_id",
        "nombre",
        "activo",
        "orden",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_provincias_inicia_sin_catalogo_base():
    """Valida que la migracion no cargue provincias iniciales."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        total = get_db().execute(
            "SELECT COUNT(*) AS total FROM provincias"
        ).fetchone()["total"]

    assert total == 0


def test_provincias_rechaza_nombre_vacio():
    """Valida que nombre no admita texto vacio ni espacios."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = _crear_pais()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pais["id"], "   ", 1, 10, "2026-01-01 10:00:00"),
            )


def test_provincias_rechaza_pais_inexistente():
    """Valida integridad referencial contra paises."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (999, "Santa Fe", 1, 10, "2026-01-01 10:00:00"),
            )


def test_provincias_rechaza_nombre_duplicado_en_mismo_pais_sin_distinguir_mayusculas():
    """Valida unicidad de provincia por pais con COLLATE NOCASE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = _crear_pais()

        get_db().execute(
            """
            INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pais["id"], "Santa Fe", 1, 10, "2026-01-01 10:00:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pais["id"], "santa fe", 1, 20, "2026-01-01 10:00:00"),
            )


def test_provincias_permite_mismo_nombre_en_distinto_pais():
    """Valida que la unicidad de nombre sea por pais."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais("Argentina", "AR")
        uruguay = _crear_pais("Uruguay", "UY")

        get_db().execute(
            """
            INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            (argentina["id"], "Santa Fe", 1, 10, "2026-01-01 10:00:00"),
        )
        get_db().execute(
            """
            INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            (uruguay["id"], "Santa Fe", 1, 10, "2026-01-01 10:00:00"),
        )

        total = get_db().execute(
            "SELECT COUNT(*) AS total FROM provincias WHERE nombre = ?",
            ("Santa Fe",),
        ).fetchone()["total"]

    assert total == 2


def test_provincias_rechaza_activo_invalido():
    """Valida que activo sea booleano entero 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = _crear_pais()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pais["id"], "Santa Fe", 2, 10, "2026-01-01 10:00:00"),
            )


def test_provincias_rechaza_orden_negativo():
    """Valida consistencia con maestros que no admiten orden negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = _crear_pais()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pais["id"], "Santa Fe", 1, -1, "2026-01-01 10:00:00"),
            )


def test_provincias_crea_indice_listado_por_pais():
    """Valida indice de listado por pais, activo, orden y nombre."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA index_list(provincias)").fetchall()

    index_names = {row["name"] for row in rows}

    assert "ix_provincias_pais_activo_orden" in index_names
