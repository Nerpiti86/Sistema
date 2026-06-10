import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tabla_monedas_cotizaciones():
    """Valida columnas base para cotizaciones transversales de monedas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute(
            "PRAGMA table_info(monedas_cotizaciones)"
        ).fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "moneda_origen_codigo",
        "moneda_destino_codigo",
        "fecha",
        "tipo",
        "cotizacion_1000000",
        "fuente",
        "observaciones",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_monedas_cotizaciones_permite_par_monedas_valido():
    """Valida cotizacion entre dos monedas existentes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
            """
            INSERT INTO monedas_cotizaciones (
                moneda_origen_codigo,
                moneda_destino_codigo,
                fecha,
                tipo,
                cotizacion_1000000,
                fuente,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "USD",
                "ARS",
                "2026-06-10",
                "CIERRE",
                1250500000,
                "Manual",
                "2026-06-10 13:30:00",
            ),
        )

        fila = db.execute(
            """
            SELECT moneda_origen_codigo,
                   moneda_destino_codigo,
                   fecha,
                   tipo,
                   cotizacion_1000000
            FROM monedas_cotizaciones
            WHERE moneda_origen_codigo = ?
              AND moneda_destino_codigo = ?
              AND fecha = ?
              AND tipo = ?
            """,
            ("USD", "ARS", "2026-06-10", "CIERRE"),
        ).fetchone()

    assert fila is not None
    assert fila["moneda_origen_codigo"] == "USD"
    assert fila["moneda_destino_codigo"] == "ARS"
    assert fila["cotizacion_1000000"] == 1250500000


def test_monedas_cotizaciones_requiere_monedas_existentes():
    """Valida integridad contra el maestro transversal monedas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas_cotizaciones (
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    fecha,
                    tipo,
                    cotizacion_1000000,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "GBP",
                    "ARS",
                    "2026-06-10",
                    "CIERRE",
                    1500000000,
                    "2026-06-10 13:30:00",
                ),
            )


def test_monedas_cotizaciones_rechaza_misma_moneda():
    """Valida que una cotizacion no relacione una moneda consigo misma."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas_cotizaciones (
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    fecha,
                    tipo,
                    cotizacion_1000000,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "ARS",
                    "ARS",
                    "2026-06-10",
                    "CIERRE",
                    1000000,
                    "2026-06-10 13:30:00",
                ),
            )


def test_monedas_cotizaciones_rechaza_fecha_invalida():
    """Valida formato mensual basico de fecha ISO."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas_cotizaciones (
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    fecha,
                    tipo,
                    cotizacion_1000000,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "USD",
                    "ARS",
                    "2026-13-10",
                    "CIERRE",
                    1250500000,
                    "2026-06-10 13:30:00",
                ),
            )


def test_monedas_cotizaciones_rechaza_tipo_invalido():
    """Valida tipos cerrados de cotizacion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas_cotizaciones (
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    fecha,
                    tipo,
                    cotizacion_1000000,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "USD",
                    "ARS",
                    "2026-06-10",
                    "OFICIAL",
                    1250500000,
                    "2026-06-10 13:30:00",
                ),
            )


def test_monedas_cotizaciones_rechaza_cotizacion_no_positiva():
    """Valida cotizacion como entero positivo escalado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO monedas_cotizaciones (
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    fecha,
                    tipo,
                    cotizacion_1000000,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "USD",
                    "ARS",
                    "2026-06-10",
                    "CIERRE",
                    0,
                    "2026-06-10 13:30:00",
                ),
            )


def test_monedas_cotizaciones_par_fecha_tipo_es_unico():
    """Valida una unica cotizacion por par, fecha y tipo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
            """
            INSERT INTO monedas_cotizaciones (
                moneda_origen_codigo,
                moneda_destino_codigo,
                fecha,
                tipo,
                cotizacion_1000000,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "USD",
                "ARS",
                "2026-06-10",
                "CIERRE",
                1250500000,
                "2026-06-10 13:30:00",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO monedas_cotizaciones (
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    fecha,
                    tipo,
                    cotizacion_1000000,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "USD",
                    "ARS",
                    "2026-06-10",
                    "CIERRE",
                    1250600000,
                    "2026-06-10 13:31:00",
                ),
            )
