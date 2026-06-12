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


def test_migracion_carga_catalogo_inicial_bcra():
    """Valida carga inicial de bancos recibida desde nomina BCRA."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        bancos = get_db().execute(
            """
            SELECT codigo, nombre
            FROM bancos
            ORDER BY CAST(codigo AS INTEGER)
            """
        ).fetchall()

    codigos = {banco["codigo"] for banco in bancos}

    assert len(bancos) == 73
    assert "7" in codigos
    assert "65" in codigos
    assert "285" in codigos
    assert "65203" in codigos


def test_bancos_rechaza_codigo_duplicado():
    """Valida que codigo BCRA sea unico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("7", "Banco duplicado", 1, 999, "2026-01-01 10:00:00"),
            )


def test_bancos_rechaza_codigo_invalido():
    """Valida formato obligatorio de codigo BCRA numerico."""
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
                ("99999", "Banco prueba", 2, 10, "2026-01-01 10:00:00"),
            )
