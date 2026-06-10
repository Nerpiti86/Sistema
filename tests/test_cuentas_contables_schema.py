import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tabla_cuentas_contables():
    """Valida columnas base del maestro cuentas_contables."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute(
            "PRAGMA table_info(cuentas_contables)"
        ).fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "cuenta",
        "descripcion",
        "saldo_habitual",
        "naturaleza",
        "imputable",
        "monetaria",
        "sumarizadora",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_cuentas_contables_permite_jerarquia_caja_ars():
    """Valida jerarquia real usando sumarizadora como codigo de cuenta padre."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        cuentas = [
            (
                "1.0.00.00.000",
                "ACTIVO",
                "DEBE",
                "PATRIMONIAL",
                0,
                1,
                None,
            ),
            (
                "1.1.00.00.000",
                "ACTIVO CORRIENTE",
                "DEBE",
                "PATRIMONIAL",
                0,
                1,
                "1.0.00.00.000",
            ),
            (
                "1.1.01.00.000",
                "CAJAS Y BANCOS",
                "DEBE",
                "PATRIMONIAL",
                0,
                1,
                "1.1.00.00.000",
            ),
            (
                "1.1.01.01.000",
                "CAJAS",
                "DEBE",
                "PATRIMONIAL",
                0,
                1,
                "1.1.01.00.000",
            ),
            (
                "1.1.01.01.001",
                "CAJA ARS",
                "DEBE",
                "PATRIMONIAL",
                1,
                1,
                "1.1.01.01.000",
            ),
        ]

        db.executemany(
            """
            INSERT INTO cuentas_contables (
                cuenta,
                descripcion,
                saldo_habitual,
                naturaleza,
                imputable,
                monetaria,
                sumarizadora,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (*cuenta, "2026-01-01 10:00:00")
                for cuenta in cuentas
            ],
        )

        row = db.execute(
            """
            SELECT
                cuenta,
                descripcion,
                saldo_habitual,
                naturaleza,
                imputable,
                monetaria,
                sumarizadora
            FROM cuentas_contables
            WHERE cuenta = ?
            LIMIT 1
            """,
            ("1.1.01.01.001",),
        ).fetchone()

    assert row is not None
    assert row["cuenta"] == "1.1.01.01.001"
    assert row["descripcion"] == "CAJA ARS"
    assert row["saldo_habitual"] == "DEBE"
    assert row["naturaleza"] == "PATRIMONIAL"
    assert row["imputable"] == 1
    assert row["monetaria"] == 1
    assert row["sumarizadora"] == "1.1.01.01.000"


def test_cuentas_contables_rechaza_cuenta_duplicada():
    """Valida que cuenta sea codigo unico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
            """
            INSERT INTO cuentas_contables (
                cuenta,
                descripcion,
                saldo_habitual,
                naturaleza,
                imputable,
                monetaria,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("1.1.01.01.001", "CAJA ARS", "DEBE", "PATRIMONIAL", 1, 1, "2026-01-01 10:00:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "1.1.01.01.001",
                    "CAJA ARS DUPLICADA",
                    "DEBE",
                    "PATRIMONIAL",
                    1,
                    1,
                ),
            )


def test_cuentas_contables_rechaza_formato_cuenta_invalido():
    """Valida formato obligatorio 9.9.99.99.999."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("1.1.1.01.001", "CUENTA MALA", "DEBE", "PATRIMONIAL", 1, 1),
            )


def test_cuentas_contables_rechaza_saldo_habitual_invalido():
    """Valida saldo_habitual cerrado a DEBE o HABER."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("1.1.01.01.001", "CAJA ARS", "AMBOS", "PATRIMONIAL", 1, 1),
            )


def test_cuentas_contables_rechaza_naturaleza_invalida():
    """Valida naturaleza cerrada a PATRIMONIAL o RESULTADO."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("1.1.01.01.001", "CAJA ARS", "DEBE", "OTRA", 1, 1),
            )


def test_cuentas_contables_rechaza_imputable_invalido():
    """Valida imputable cerrado a 0 o 1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("1.1.01.01.001", "CAJA ARS", "DEBE", "PATRIMONIAL", 2, 1),
            )


def test_cuentas_contables_rechaza_monetaria_invalida():
    """Valida monetaria cerrado a 0 o 1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("1.1.01.01.001", "CAJA ARS", "DEBE", "PATRIMONIAL", 1, 2),
            )


def test_cuentas_contables_rechaza_sumarizadora_inexistente():
    """Valida que sumarizadora apunte a una cuenta padre existente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria,
                    sumarizadora
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "1.1.01.01.001",
                    "CAJA ARS",
                    "DEBE",
                    "PATRIMONIAL",
                    1,
                    1,
                    "1.1.01.01.000",
                ),
            )


def test_cuentas_contables_rechaza_sumarizadora_igual_a_cuenta():
    """Valida que una cuenta no pueda ser su propia sumarizadora."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria,
                    sumarizadora
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "1.1.01.01.001",
                    "CAJA ARS",
                    "DEBE",
                    "PATRIMONIAL",
                    1,
                    1,
                    "1.1.01.01.001",
                ),
            )


def test_cuentas_contables_imputable_y_monetaria_son_enteros_booleanos():
    """
    Valida contrato SQLite final para flags booleanos.

    Imputable y monetaria son INTEGER 0/1. El texto de pantalla se resuelve
    fuera de SQLite.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute(
            "PRAGMA table_info(cuentas_contables)"
        ).fetchall()

    columns = {row["name"]: row for row in rows}

    assert columns["imputable"]["type"].upper() == "INTEGER"
    assert columns["monetaria"]["type"].upper() == "INTEGER"
