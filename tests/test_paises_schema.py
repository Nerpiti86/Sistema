import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tabla_paises():
    """Valida columnas base del maestro comun de paises."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA table_info(paises)").fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "nombre",
        "codigo_iso",
        "activo",
        "orden",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_paises_inicia_sin_catalogo_base():
    """Valida que la migracion no cargue paises iniciales."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        total = get_db().execute(
            "SELECT COUNT(*) AS total FROM paises"
        ).fetchone()["total"]

    assert total == 0


def test_paises_rechaza_nombre_vacio():
    """Valida que nombre no admita texto vacio ni espacios."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("   ", "AR", 1, 10, "2026-01-01 10:00:00"),
            )


def test_paises_rechaza_nombre_duplicado_sin_distinguir_mayusculas():
    """Valida unicidad de nombre con COLLATE NOCASE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        get_db().execute(
            """
            INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Argentina", "AR", 1, 10, "2026-01-01 10:00:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("argentina", "ARG", 1, 20, "2026-01-01 10:00:00"),
            )


def test_paises_rechaza_codigo_iso_duplicado_sin_distinguir_mayusculas():
    """Valida unicidad de codigo_iso con COLLATE NOCASE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        get_db().execute(
            """
            INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Argentina", "AR", 1, 10, "2026-01-01 10:00:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("Republica Argentina", "ar", 1, 20, "2026-01-01 10:00:00"),
            )


def test_paises_permite_codigo_iso_nulo():
    """Valida que codigo_iso sea opcional para carga manual inicial."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        get_db().execute(
            """
            INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Argentina", None, 1, 10, "2026-01-01 10:00:00"),
        )

        total = get_db().execute(
            "SELECT COUNT(*) AS total FROM paises"
        ).fetchone()["total"]

    assert total == 1


def test_paises_rechaza_codigo_iso_largo_invalido():
    """Valida que codigo_iso admita solo codigos de 2 o 3 caracteres."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("Argentina", "ARGEN", 1, 10, "2026-01-01 10:00:00"),
            )


def test_paises_rechaza_activo_invalido():
    """Valida que activo sea booleano entero 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("Argentina", "AR", 2, 10, "2026-01-01 10:00:00"),
            )


def test_paises_rechaza_orden_negativo():
    """Valida consistencia con maestros que no admiten orden negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("Argentina", "AR", 1, -1, "2026-01-01 10:00:00"),
            )


def test_paises_crea_indice_listado():
    """Valida indice de listado por activo, orden y nombre."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA index_list(paises)").fetchall()

    index_names = {row["name"] for row in rows}

    assert "ix_paises_activo_orden" in index_names
