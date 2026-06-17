import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _columnas(tabla: str) -> set[str]:
    rows = get_db().execute(f"PRAGMA table_info({tabla})").fetchall()
    return {row["name"] for row in rows}


def _insertar_cuenta(db, cuenta: str, descripcion: str, saldo: str) -> None:
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
        (
            cuenta,
            descripcion,
            saldo,
            "PATRIMONIAL",
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )


def _insertar_grupo_cliente(db) -> int:
    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("General", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _insertar_cliente(db, cuenta_deudores: str, cuenta_anticipo: str) -> int:
    grupo_id = _insertar_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (
            razon_social,
            grupo_cliente_id,
            cuenta_deudores_ventas_codigo,
            cuenta_anticipo_clientes_codigo,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "Cliente Cobranza",
            grupo_id,
            cuenta_deudores,
            cuenta_anticipo,
            "2026-01-01 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def test_migracion_crea_tablas_clientes_cobranzas_y_caja():
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        assert {
            "id",
            "cliente_id",
            "fecha",
            "tipo_cobranza",
            "tipo_comprobante",
            "letra",
            "punto_venta",
            "numero",
            "moneda_codigo",
            "cotizacion_1000000",
            "total_centavos",
            "estado",
            "asiento_id",
            "observaciones",
            "creado_en",
            "actualizado_en",
            "confirmado_en",
            "anulado_en",
        }.issubset(_columnas("clientes_cobranzas"))

        assert {
            "id",
            "cobranza_cliente_id",
            "tipo_linea",
            "movimiento_ctacte_cancelado_id",
            "venta_comprobante_id",
            "movimiento_ctacte_generado_id",
            "importe_centavos",
            "cuenta_cancelacion_codigo",
            "orden",
            "observaciones",
        }.issubset(_columnas("clientes_cobranzas_lineas"))

        assert {
            "id",
            "fecha",
            "tipo_movimiento",
            "origen_tipo",
            "origen_id",
            "moneda_contable_codigo",
            "total_contable_centavos",
            "estado",
            "asiento_id",
            "observaciones",
            "creado_en",
            "actualizado_en",
            "confirmado_en",
            "anulado_en",
        }.issubset(_columnas("movimientos_caja"))

        assert {
            "id",
            "movimiento_caja_id",
            "medio_operativo_codigo",
            "cuenta_contable_codigo",
            "moneda_codigo",
            "fecha_valor",
            "referencia",
            "importe_nominal_centavos",
            "cotizacion_1000000",
            "importe_contable_centavos",
            "detalle",
            "orden",
        }.issubset(_columnas("movimientos_caja_lineas"))


def test_cobranza_anticipo_y_movimiento_caja_minimo_insertan():
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_cuenta(db, "1.1.01.01.001", "Caja ARS", "DEBE")
        _insertar_cuenta(db, "1.1.02.01.001", "Deudores por ventas", "DEBE")
        _insertar_cuenta(db, "2.1.01.01.001", "Anticipo de clientes", "HABER")

        cliente_id = _insertar_cliente(
            db,
            "1.1.02.01.001",
            "2.1.01.01.001",
        )

        db.execute(
            """
            INSERT INTO medios_operativos (
                codigo,
                nombre,
                tipo,
                cuenta_contable_codigo,
                moneda_codigo,
                activo,
                orden,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "1",
                "Pesos",
                "EFECTIVO",
                "1.1.01.01.001",
                "ARS",
                1,
                10,
                "2026-01-01 10:00:00",
            ),
        )

        cursor = db.execute(
            """
            INSERT INTO clientes_cobranzas (
                cliente_id,
                fecha,
                tipo_cobranza,
                tipo_comprobante,
                letra,
                punto_venta,
                numero,
                moneda_codigo,
                cotizacion_1000000,
                total_centavos,
                estado,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                "2026-06-16",
                "ANTICIPO",
                "RECIBO",
                "C",
                1,
                1,
                "ARS",
                1000000,
                100000,
                "BORRADOR",
                "2026-06-16 10:00:00",
            ),
        )
        cobranza_id = int(cursor.lastrowid)

        db.execute(
            """
            INSERT INTO clientes_cobranzas_lineas (
                cobranza_cliente_id,
                tipo_linea,
                importe_centavos,
                cuenta_cancelacion_codigo,
                orden
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                cobranza_id,
                "ANTICIPO",
                100000,
                "2.1.01.01.001",
                1,
            ),
        )

        cursor = db.execute(
            """
            INSERT INTO movimientos_caja (
                fecha,
                tipo_movimiento,
                origen_tipo,
                origen_id,
                moneda_contable_codigo,
                total_contable_centavos,
                estado,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-06-16",
                "INGRESO",
                "CLIENTES_COBRANZA",
                cobranza_id,
                "ARS",
                100000,
                "BORRADOR",
                "2026-06-16 10:00:00",
            ),
        )
        movimiento_caja_id = int(cursor.lastrowid)

        db.execute(
            """
            INSERT INTO movimientos_caja_lineas (
                movimiento_caja_id,
                medio_operativo_codigo,
                cuenta_contable_codigo,
                moneda_codigo,
                fecha_valor,
                referencia,
                importe_nominal_centavos,
                cotizacion_1000000,
                importe_contable_centavos,
                detalle,
                orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                movimiento_caja_id,
                "1",
                "1.1.01.01.001",
                "ARS",
                "2026-06-16",
                "EFECTIVO",
                100000,
                1000000,
                100000,
                "Cobro en efectivo",
                1,
            ),
        )

        lineas = db.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM movimientos_caja_lineas
            WHERE movimiento_caja_id = ?
            """,
            (movimiento_caja_id,),
        ).fetchone()

    assert lineas["cantidad"] == 1


def test_cobranza_linea_anticipo_rechaza_comprobante_asociado():
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_cuenta(db, "1.1.02.01.001", "Deudores por ventas", "DEBE")
        _insertar_cuenta(db, "2.1.01.01.001", "Anticipo de clientes", "HABER")
        cliente_id = _insertar_cliente(
            db,
            "1.1.02.01.001",
            "2.1.01.01.001",
        )

        cursor = db.execute(
            """
            INSERT INTO clientes_cobranzas (
                cliente_id,
                fecha,
                tipo_cobranza,
                tipo_comprobante,
                letra,
                punto_venta,
                numero,
                total_centavos,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                "2026-06-16",
                "ANTICIPO",
                "RECIBO",
                "C",
                1,
                1,
                100000,
                "2026-06-16 10:00:00",
            ),
        )
        cobranza_id = int(cursor.lastrowid)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO clientes_cobranzas_lineas (
                    cobranza_cliente_id,
                    tipo_linea,
                    movimiento_ctacte_cancelado_id,
                    venta_comprobante_id,
                    importe_centavos,
                    cuenta_cancelacion_codigo,
                    orden
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cobranza_id,
                    "ANTICIPO",
                    1,
                    1,
                    100000,
                    "2.1.01.01.001",
                    1,
                ),
            )


def test_asientos_contables_permite_tipos_cobranza_y_caja_en_schema():
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        row = get_db().execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'asientos_contables'
            """
        ).fetchone()

    assert "'COBRANZA'" in row["sql"]
    assert "'CAJA'" in row["sql"]
