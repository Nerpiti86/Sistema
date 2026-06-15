import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _crear_grupo_cliente(db) -> int:
    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("General", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cliente(db) -> int:
    grupo_id = _crear_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (razon_social, grupo_cliente_id, creado_en)
        VALUES (?, ?, ?)
        """,
        ("Cliente Cuenta Corriente", grupo_id, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def test_migracion_crea_tabla_clientes_cuenta_corriente_movimientos():
    """
    Contrato: la cuenta corriente de clientes nace como movimientos DEBE/HABER.

    El saldo no se persiste: se calcula desde los movimientos confirmados.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute(
            "PRAGMA table_info(clientes_cuenta_corriente_movimientos)"
        ).fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "cliente_id",
        "fecha",
        "tipo_movimiento",
        "descripcion",
        "moneda_codigo",
        "debe_centavos",
        "haber_centavos",
        "estado",
        "origen_tipo",
        "origen_id",
        "asiento_id",
        "creado_en",
        "actualizado_en",
        "confirmado_en",
        "anulado_en",
    }.issubset(column_names)

    assert "saldo_centavos" not in column_names
    assert "saldo_a_favor_centavos" not in column_names


def test_clientes_ctacte_permite_movimiento_debe_factura():
    """
    Contrato: una factura de cliente impacta al DEBE de la cuenta corriente.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        db.execute(
            """
            INSERT INTO clientes_cuenta_corriente_movimientos (
                cliente_id,
                fecha,
                tipo_movimiento,
                descripcion,
                moneda_codigo,
                debe_centavos,
                haber_centavos,
                estado,
                origen_tipo,
                origen_id,
                creado_en,
                confirmado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                "2026-01-15",
                "FACTURA",
                "Factura pendiente",
                "ARS",
                100000,
                0,
                "CONFIRMADO",
                "VENTA",
                1,
                "2026-01-15 10:00:00",
                "2026-01-15 10:01:00",
            ),
        )

        movimiento = db.execute(
            """
            SELECT debe_centavos, haber_centavos
            FROM clientes_cuenta_corriente_movimientos
            WHERE cliente_id = ?
            """,
            (cliente_id,),
        ).fetchone()

    assert movimiento["debe_centavos"] == 100000
    assert movimiento["haber_centavos"] == 0


def test_clientes_ctacte_permite_movimiento_haber_anticipo():
    """
    Contrato: una cobranza sin factura impacta al HABER como anticipo.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        db.execute(
            """
            INSERT INTO clientes_cuenta_corriente_movimientos (
                cliente_id,
                fecha,
                tipo_movimiento,
                descripcion,
                moneda_codigo,
                debe_centavos,
                haber_centavos,
                estado,
                origen_tipo,
                origen_id,
                creado_en,
                confirmado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                "2026-01-15",
                "ANTICIPO",
                "Cobranza sin factura",
                "ARS",
                0,
                100000,
                "CONFIRMADO",
                "COBRANZA",
                1,
                "2026-01-15 10:00:00",
                "2026-01-15 10:01:00",
            ),
        )

        movimiento = db.execute(
            """
            SELECT debe_centavos, haber_centavos
            FROM clientes_cuenta_corriente_movimientos
            WHERE cliente_id = ?
            """,
            (cliente_id,),
        ).fetchone()

    assert movimiento["debe_centavos"] == 0
    assert movimiento["haber_centavos"] == 100000


def test_clientes_ctacte_rechaza_movimiento_con_debe_y_haber():
    """
    Contrato: cada movimiento usa un solo lado, DEBE o HABER.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO clientes_cuenta_corriente_movimientos (
                    cliente_id,
                    fecha,
                    tipo_movimiento,
                    descripcion,
                    moneda_codigo,
                    debe_centavos,
                    haber_centavos,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente_id,
                    "2026-01-15",
                    "AJUSTE",
                    "Movimiento invalido",
                    "ARS",
                    100000,
                    100000,
                    "2026-01-15 10:00:00",
                ),
            )


def test_clientes_ctacte_rechaza_movimiento_sin_importe():
    """
    Contrato: cada movimiento debe tener importe positivo en DEBE o HABER.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO clientes_cuenta_corriente_movimientos (
                    cliente_id,
                    fecha,
                    tipo_movimiento,
                    descripcion,
                    moneda_codigo,
                    debe_centavos,
                    haber_centavos,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente_id,
                    "2026-01-15",
                    "AJUSTE",
                    "Movimiento sin importe",
                    "ARS",
                    0,
                    0,
                    "2026-01-15 10:00:00",
                ),
            )


def test_clientes_ctacte_rechaza_tipo_movimiento_invalido():
    """
    Contrato: los tipos de movimiento nacen cerrados para evitar ambiguedad.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO clientes_cuenta_corriente_movimientos (
                    cliente_id,
                    fecha,
                    tipo_movimiento,
                    descripcion,
                    moneda_codigo,
                    debe_centavos,
                    haber_centavos,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente_id,
                    "2026-01-15",
                    "VENTA_GENERICA",
                    "Tipo invalido",
                    "ARS",
                    100000,
                    0,
                    "2026-01-15 10:00:00",
                ),
            )


def test_clientes_ctacte_rechaza_origen_incompleto():
    """
    Contrato: origen_tipo y origen_id se informan juntos o ambos quedan nulos.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO clientes_cuenta_corriente_movimientos (
                    cliente_id,
                    fecha,
                    tipo_movimiento,
                    descripcion,
                    moneda_codigo,
                    debe_centavos,
                    haber_centavos,
                    origen_tipo,
                    origen_id,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente_id,
                    "2026-01-15",
                    "FACTURA",
                    "Origen incompleto",
                    "ARS",
                    100000,
                    0,
                    "VENTA",
                    None,
                    "2026-01-15 10:00:00",
                ),
            )


def test_clientes_ctacte_rechaza_cliente_inexistente():
    """
    Contrato: todo movimiento pertenece a un cliente existente.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes_cuenta_corriente_movimientos (
                    cliente_id,
                    fecha,
                    tipo_movimiento,
                    descripcion,
                    moneda_codigo,
                    debe_centavos,
                    haber_centavos,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    999,
                    "2026-01-15",
                    "FACTURA",
                    "Cliente inexistente",
                    "ARS",
                    100000,
                    0,
                    "2026-01-15 10:00:00",
                ),
            )
