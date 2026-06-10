import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tabla_monedas():
    """Valida columnas base del maestro transversal monedas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute(
            "PRAGMA table_info(monedas)"
        ).fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "codigo",
        "nombre",
        "simbolo",
        "decimales",
        "activa",
        "orden",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_monedas_iniciales_quedan_cargadas():
    """Valida monedas base compartidas por gestion y contabilidad."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute(
            """
            SELECT codigo, nombre, simbolo, decimales, activa, orden
            FROM monedas
            ORDER BY orden
            """
        ).fetchall()

    monedas = {row["codigo"]: row for row in rows}

    assert {"ARS", "USD", "EUR"}.issubset(monedas)
    assert monedas["ARS"]["nombre"] == "Peso argentino"
    assert monedas["ARS"]["simbolo"] == "$"
    assert monedas["ARS"]["decimales"] == 2
    assert monedas["ARS"]["activa"] == 1


def test_monedas_rechaza_codigo_duplicado():
    """Valida que codigo ISO sea unico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas (
                    codigo,
                    nombre,
                    simbolo,
                    decimales,
                    activa,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "ARS",
                    "Peso argentino duplicado",
                    "$",
                    2,
                    1,
                    99,
                    "2026-01-01 10:00:00",
                ),
            )


def test_monedas_rechaza_codigo_invalido():
    """Valida formato obligatorio de codigo moneda AAA."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas (
                    codigo,
                    nombre,
                    simbolo,
                    decimales,
                    activa,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "ars",
                    "Peso argentino",
                    "$",
                    2,
                    1,
                    10,
                    "2026-01-01 10:00:00",
                ),
            )


def test_monedas_rechaza_decimales_invalidos():
    """Valida que decimales sea entero dentro del rango permitido."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas (
                    codigo,
                    nombre,
                    simbolo,
                    decimales,
                    activa,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "JPY",
                    "Yen japones",
                    "¥",
                    9,
                    1,
                    40,
                    "2026-01-01 10:00:00",
                ),
            )


def test_monedas_rechaza_activa_invalida():
    """Valida que activa sea booleano entero 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas (
                    codigo,
                    nombre,
                    simbolo,
                    decimales,
                    activa,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "BRL",
                    "Real brasileno",
                    "R$",
                    2,
                    2,
                    40,
                    "2026-01-01 10:00:00",
                ),
            )


def test_monedas_activa_es_entero_booleano():
    """Valida contrato SQLite final para flag activa."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute(
            "PRAGMA table_info(monedas)"
        ).fetchall()

    columns = {row["name"]: row for row in rows}

    assert columns["activa"]["type"].upper() == "INTEGER"
