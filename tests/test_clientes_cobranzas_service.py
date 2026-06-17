import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.clientes_cobranzas_service import (
    crear_cobranza_aplicada_confirmada,
)
from app.gestion.clientes_cuenta_corriente_service import (
    crear_movimiento_debe_cliente,
)


def _crear_cuenta(
    db,
    cuenta: str,
    descripcion: str,
    saldo_habitual: str,
    naturaleza: str,
    monetaria: int,
) -> str:
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
            saldo_habitual,
            naturaleza,
            1,
            monetaria,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def _obtener_o_crear_grupo_cliente(db) -> int:
    fila = db.execute(
        """
        SELECT id
        FROM grupos_clientes
        WHERE nombre = ?
        LIMIT 1
        """,
        ("General",),
    ).fetchone()

    if fila is not None:
        return int(fila["id"])

    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("General", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cliente(
    db,
    cuenta_deudores_codigo: str,
    cuenta_anticipo_codigo: str,
) -> int:
    grupo_id = _obtener_o_crear_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (
            razon_social,
            grupo_cliente_id,
            cuenta_deudores_ventas_codigo,
            cuenta_anticipo_clientes_codigo,
            activo,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Cliente Cobranza Service",
            grupo_id,
            cuenta_deudores_codigo,
            cuenta_anticipo_codigo,
            1,
            "2026-01-01 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _obtener_o_crear_ejercicio(db) -> int:
    fila = db.execute(
        """
        SELECT id
        FROM ejercicios_contables
        WHERE fecha_desde <= ?
          AND fecha_hasta >= ?
          AND estado = ?
        ORDER BY id
        LIMIT 1
        """,
        ("2026-06-17", "2026-06-17", "ABIERTO"),
    ).fetchone()

    if fila is not None:
        return int(fila["id"])

    cursor = db.execute(
        """
        INSERT INTO ejercicios_contables (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            creado_en,
            fase_cierre,
            bloqueado,
            es_primer_ejercicio
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "2026",
            "Ejercicio test cobranzas",
            "2026-01-01",
            "2026-12-31",
            "ABIERTO",
            1,
            "2026-01-01 00:00:00",
            "ABIERTO",
            0,
            1,
        ),
    )
    return int(cursor.lastrowid)


def _crear_medio_operativo_efectivo(db, cuenta_caja_codigo: str) -> None:
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
            cuenta_caja_codigo,
            "ARS",
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )


def _crear_factura_confirmada(db, cliente_id: int, total_centavos: int) -> int:
    cursor = db.execute(
        """
        INSERT INTO ventas_comprobantes (
            cliente_id,
            fecha,
            fecha_vencimiento,
            tipo_comprobante,
            tipo_comprobante_codigo,
            letra,
            punto_venta,
            numero,
            moneda_codigo,
            cotizacion_centavos,
            subtotal_centavos,
            descuento_centavos,
            recargo_centavos,
            iva_centavos,
            total_centavos,
            estado,
            creado_en,
            confirmado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cliente_id,
            "2026-06-10",
            "2026-07-10",
            "FACTURA",
            "011",
            "C",
            1,
            100,
            "ARS",
            100,
            total_centavos,
            0,
            0,
            0,
            total_centavos,
            "CONFIRMADO",
            "2026-06-10 10:00:00",
            "2026-06-10 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _preparar_base_cobranza(apply=True):
    if apply:
        apply_migrations()

    db = get_db()
    _obtener_o_crear_ejercicio(db)

    cuenta_caja = _crear_cuenta(
        db,
        "1.1.01.01.901",
        "Caja ARS test cobranzas",
        "DEBE",
        "PATRIMONIAL",
        1,
    )
    cuenta_deudores = _crear_cuenta(
        db,
        "1.1.02.01.901",
        "Deudores por ventas test cobranzas",
        "DEBE",
        "PATRIMONIAL",
        1,
    )
    cuenta_anticipo = _crear_cuenta(
        db,
        "2.1.01.01.901",
        "Anticipo clientes test cobranzas",
        "HABER",
        "PATRIMONIAL",
        0,
    )
    _crear_medio_operativo_efectivo(db, cuenta_caja)

    cliente_id = _crear_cliente(db, cuenta_deudores, cuenta_anticipo)
    comprobante_id = _crear_factura_confirmada(db, cliente_id, 3500000)
    movimiento_debe = crear_movimiento_debe_cliente(
        {
            "cliente_id": cliente_id,
            "fecha": "2026-06-10",
            "tipo_movimiento": "FACTURA",
            "descripcion": "FC C 0001-00000100",
            "moneda_codigo": "ARS",
            "estado": "CONFIRMADO",
            "origen_tipo": "VENTA_COMPROBANTE",
            "origen_id": comprobante_id,
            "importe_centavos": 3500000,
        }
    )

    return {
        "cliente_id": cliente_id,
        "comprobante_id": comprobante_id,
        "movimiento_debe_id": movimiento_debe["id"],
        "cuenta_caja": cuenta_caja,
        "cuenta_deudores": cuenta_deudores,
    }


def test_cobranza_aplicada_confirmada_impacta_caja_asiento_y_cuenta_corriente():
    """
    Contrato: una cobranza aplicada simple confirmada impacta cobranza, caja,
    asiento y cuenta corriente en una unica transaccion.
    """
    app = create_app(TestConfig)

    with app.app_context():
        base = _preparar_base_cobranza()

        resultado = crear_cobranza_aplicada_confirmada(
            {
                "cliente_id": base["cliente_id"],
                "fecha": "2026-06-17",
                "tipo_cobranza": "APLICADA",
                "letra": "C",
                "punto_venta": 1,
                "numero": 1,
                "moneda_codigo": "ARS",
                "total_centavos": 3500000,
                "observaciones": "Cobro factura test",
            },
            [
                {
                    "tipo_linea": "FACTURA",
                    "movimiento_ctacte_cancelado_id": base["movimiento_debe_id"],
                    "venta_comprobante_id": base["comprobante_id"],
                    "importe_centavos": 3500000,
                }
            ],
            [
                {
                    "medio_operativo_codigo": "1",
                    "importe_centavos": 3500000,
                    "fecha_valor": "2026-06-17",
                    "referencia": "EFECTIVO",
                    "detalle": "Cobro efectivo",
                }
            ],
        )

        db = get_db()
        asiento_detalles = db.execute(
            """
            SELECT cuenta_contable_codigo, debe_centavos, haber_centavos
            FROM asientos_contables_detalle
            WHERE asiento_id = ?
            ORDER BY renglon
            """,
            (resultado["asiento"]["id"],),
        ).fetchall()
        saldo = db.execute(
            """
            SELECT
                COALESCE(SUM(debe_centavos), 0) AS debe,
                COALESCE(SUM(haber_centavos), 0) AS haber
            FROM clientes_cuenta_corriente_movimientos
            WHERE cliente_id = ?
              AND estado = 'CONFIRMADO'
            """,
            (base["cliente_id"],),
        ).fetchone()

    assert resultado["cobranza"]["estado"] == "CONFIRMADO"
    assert resultado["cobranza"]["asiento_id"] == resultado["asiento"]["id"]
    assert resultado["cobranza"]["lineas"][0]["movimiento_ctacte_generado_id"] == resultado[
        "movimiento_cuenta_corriente"
    ]["id"]
    assert resultado["movimiento_caja"]["estado"] == "CONFIRMADO"
    assert resultado["movimiento_caja"]["origen_tipo"] == "CLIENTE_COBRANZA"
    assert resultado["movimiento_caja"]["origen_id"] == resultado["cobranza"]["id"]
    assert resultado["movimiento_caja"]["asiento_id"] == resultado["asiento"]["id"]
    assert resultado["movimiento_cuenta_corriente"]["tipo_movimiento"] == "COBRANZA"
    assert resultado["movimiento_cuenta_corriente"]["haber_centavos"] == 3500000
    assert resultado["asiento"]["tipo"] == "COBRANZA"
    assert asiento_detalles[0]["cuenta_contable_codigo"] == base["cuenta_caja"]
    assert asiento_detalles[0]["debe_centavos"] == 3500000
    assert asiento_detalles[1]["cuenta_contable_codigo"] == base["cuenta_deudores"]
    assert asiento_detalles[1]["haber_centavos"] == 3500000
    assert int(saldo["debe"]) == 3500000
    assert int(saldo["haber"]) == 3500000


def test_cobranza_aplicada_rechaza_total_caja_distinto_y_no_persiste_parcial():
    """
    Contrato: si el total de caja no coincide con la cobranza, no queda impacto.
    """
    app = create_app(TestConfig)

    with app.app_context():
        base = _preparar_base_cobranza()

        with pytest.raises(ValueError, match="total de caja"):
            crear_cobranza_aplicada_confirmada(
                {
                    "cliente_id": base["cliente_id"],
                    "fecha": "2026-06-17",
                    "tipo_cobranza": "APLICADA",
                    "total_centavos": 3500000,
                },
                [
                    {
                        "tipo_linea": "FACTURA",
                        "movimiento_ctacte_cancelado_id": base["movimiento_debe_id"],
                        "venta_comprobante_id": base["comprobante_id"],
                        "importe_centavos": 3500000,
                    }
                ],
                [
                    {
                        "medio_operativo_codigo": "1",
                        "importe_centavos": 3400000,
                    }
                ],
            )

        db = get_db()
        cobranzas = db.execute("SELECT COUNT(*) AS cantidad FROM clientes_cobranzas").fetchone()
        movimientos_caja = db.execute("SELECT COUNT(*) AS cantidad FROM movimientos_caja").fetchone()
        asientos_cobranza = db.execute(
            "SELECT COUNT(*) AS cantidad FROM asientos_contables WHERE tipo = 'COBRANZA'"
        ).fetchone()
        movimientos_cobranza = db.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM clientes_cuenta_corriente_movimientos
            WHERE tipo_movimiento = 'COBRANZA'
            """
        ).fetchone()

    assert int(cobranzas["cantidad"]) == 0
    assert int(movimientos_caja["cantidad"]) == 0
    assert int(asientos_cobranza["cantidad"]) == 0
    assert int(movimientos_cobranza["cantidad"]) == 0
