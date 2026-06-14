import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tabla_grupos_clientes():
    """Valida columnas base del maestro de grupos de clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA table_info(grupos_clientes)").fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "nombre",
        "activo",
        "orden",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_grupos_clientes_inicia_sin_catalogo_base():
    """Valida que la migracion no cargue grupos iniciales."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        total = get_db().execute(
            "SELECT COUNT(*) AS total FROM grupos_clientes"
        ).fetchone()["total"]

    assert total == 0


def test_grupos_clientes_rechaza_nombre_vacio():
    """Valida que nombre no admita texto vacio ni espacios."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?)
                """,
                ("   ", 1, 10, "2026-01-01 10:00:00"),
            )


def test_grupos_clientes_rechaza_nombre_duplicado_sin_distinguir_mayusculas():
    """Valida unicidad de nombre con COLLATE NOCASE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        get_db().execute(
            """
            INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?)
            """,
            ("Particular", 1, 10, "2026-01-01 10:00:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?)
                """,
                ("particular", 1, 20, "2026-01-01 10:00:00"),
            )


def test_grupos_clientes_rechaza_activo_invalido():
    """Valida que activo sea booleano entero 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?)
                """,
                ("Mayorista", 2, 10, "2026-01-01 10:00:00"),
            )


def test_grupos_clientes_rechaza_orden_negativo():
    """Valida consistencia con maestros que no admiten orden negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?)
                """,
                ("Mayorista", 1, -1, "2026-01-01 10:00:00"),
            )


def test_grupos_clientes_crea_indice_listado():
    """Valida indice de listado por activo, orden y nombre."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA index_list(grupos_clientes)").fetchall()

    index_names = {row["name"] for row in rows}

    assert "ix_grupos_clientes_activo_orden" in index_names
