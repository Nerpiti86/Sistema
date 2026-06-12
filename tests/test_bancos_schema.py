import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tabla_bancos():
    """Valida columnas base del maestro transversal bancos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA table_info(bancos)").fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "codigo",
        "nombre",
        "activo",
        "orden",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_bancos_rechaza_codigo_duplicado():
    """Valida que codigo BCRA sea unico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            """
            INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("AAA00", "Banco prueba", 1, 10, "2026-01-01 10:00:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("AAA00", "Banco prueba duplicado", 1, 20, "2026-01-01 10:00:00"),
            )


def test_bancos_rechaza_codigo_invalido():
    """Valida formato obligatorio de codigo BCRA de cinco caracteres."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("A1", "Banco prueba", 1, 10, "2026-01-01 10:00:00"),
            )


def test_bancos_rechaza_activo_invalido():
    """Valida que activo sea booleano entero 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("BBB00", "Banco prueba", 2, 10, "2026-01-01 10:00:00"),
            )
