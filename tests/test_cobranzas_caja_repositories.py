import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.caja.movimientos_caja_repository import (
    crear_movimiento_caja,
    obtener_movimiento_caja_por_id,
)
from app.gestion.clientes_cobranzas_repository import (
    crear_cobranza_cliente,
    obtener_cobranza_cliente_por_id,
)


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


def _insertar_cliente(db) -> int:
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
            "Cliente Repository",
            grupo_id,
            "1.1.02.01.001",
            "2.1.01.01.001",
            "2026-01-01 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _insertar_medio_operativo_efectivo(db) -> None:
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
            1,
            "2026-01-01 10:00:00",
        ),
    )


def _preparar_datos_base_en_contexto() -> int:
    """
    Prepara datos sobre la conexion activa.

    TestConfig usa SQLite :memory:, por eso esta funcion debe ejecutarse dentro
    del mismo app_context del test que luego invoca los repositories.
    """
    apply_migrations()
    db = get_db()

    _insertar_cuenta(db, "1.1.01.01.001", "Caja ARS", "DEBE")
    _insertar_cuenta(db, "1.1.02.01.001", "Deudores por ventas", "DEBE")
    _insertar_cuenta(db, "2.1.01.01.001", "Anticipo de clientes", "HABER")
    _insertar_medio_operativo_efectivo(db)
    return _insertar_cliente(db)


def test_crear_cobranza_cliente_anticipo_con_linea():
    """
    Contrato: el repository de cobranzas crea cabecera y lineas funcionales
    sin generar asiento ni cuenta corriente.
    """
    app = create_app(TestConfig)

    with app.app_context():
        cliente_id = _preparar_datos_base_en_contexto()

        cobranza = crear_cobranza_cliente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-06-17",
                "tipo_cobranza": "ANTICIPO",
                "tipo_comprobante": "RECIBO",
                "letra": "C",
                "punto_venta": 1,
                "numero": 1,
                "moneda_codigo": "ARS",
                "cotizacion_1000000": 1000000,
                "total_centavos": 100000,
                "estado": "BORRADOR",
            },
            [
                {
                    "tipo_linea": "ANTICIPO",
                    "importe_centavos": 100000,
                    "cuenta_cancelacion_codigo": "2.1.01.01.001",
                    "orden": 1,
                }
            ],
        )

        recuperada = obtener_cobranza_cliente_por_id(cobranza["id"])

    assert cobranza["cliente_id"] == cliente_id
    assert cobranza["total_centavos"] == 100000
    assert cobranza["lineas"][0]["tipo_linea"] == "ANTICIPO"
    assert recuperada is not None
    assert recuperada["lineas"][0]["cuenta_cancelacion_codigo"] == "2.1.01.01.001"


def test_crear_movimiento_caja_con_linea_efectivo():
    """
    Contrato: el repository de caja crea cabecera y lineas financieras
    con snapshot de medio, cuenta, moneda e importe contable.
    """
    app = create_app(TestConfig)

    with app.app_context():
        _preparar_datos_base_en_contexto()

        movimiento = crear_movimiento_caja(
            {
                "fecha": "2026-06-17",
                "tipo_movimiento": "INGRESO",
                "origen_tipo": "CLIENTES_COBRANZA",
                "origen_id": 1,
                "moneda_contable_codigo": "ARS",
                "total_contable_centavos": 100000,
                "estado": "BORRADOR",
            },
            [
                {
                    "medio_operativo_codigo": "1",
                    "cuenta_contable_codigo": "1.1.01.01.001",
                    "moneda_codigo": "ARS",
                    "fecha_valor": "2026-06-17",
                    "referencia": "EFECTIVO",
                    "importe_nominal_centavos": 100000,
                    "cotizacion_1000000": 1000000,
                    "importe_contable_centavos": 100000,
                    "detalle": "Cobro en efectivo",
                    "orden": 1,
                }
            ],
        )

        recuperado = obtener_movimiento_caja_por_id(movimiento["id"])

    assert movimiento["total_contable_centavos"] == 100000
    assert movimiento["lineas"][0]["medio_operativo_codigo"] == "1"
    assert movimiento["lineas"][0]["cuenta_contable_codigo"] == "1.1.01.01.001"
    assert recuperado is not None
    assert recuperado["lineas"][0]["medio_operativo_nombre"] == "Pesos"


def test_cobranza_rechaza_total_distinto_a_lineas():
    """
    Contrato: el total de cobranza debe coincidir con la suma de lineas.
    """
    app = create_app(TestConfig)

    with app.app_context():
        cliente_id = _preparar_datos_base_en_contexto()

        with pytest.raises(ValueError, match="total de lineas"):
            crear_cobranza_cliente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-06-17",
                    "tipo_cobranza": "ANTICIPO",
                    "total_centavos": 100000,
                },
                [
                    {
                        "tipo_linea": "ANTICIPO",
                        "importe_centavos": 90000,
                        "cuenta_cancelacion_codigo": "2.1.01.01.001",
                    }
                ],
            )


def test_movimiento_caja_rechaza_total_distinto_a_lineas():
    """
    Contrato: el total contable de caja debe coincidir con la suma de lineas.
    """
    app = create_app(TestConfig)

    with app.app_context():
        _preparar_datos_base_en_contexto()

        with pytest.raises(ValueError, match="total de lineas"):
            crear_movimiento_caja(
                {
                    "fecha": "2026-06-17",
                    "tipo_movimiento": "INGRESO",
                    "total_contable_centavos": 100000,
                },
                [
                    {
                        "medio_operativo_codigo": "1",
                        "cuenta_contable_codigo": "1.1.01.01.001",
                        "moneda_codigo": "ARS",
                        "importe_nominal_centavos": 90000,
                        "cotizacion_1000000": 1000000,
                        "importe_contable_centavos": 90000,
                    }
                ],
            )


def test_cobranza_rechaza_linea_aplicada_sin_referencias():
    """
    Contrato: una linea aplicada a FC/ND debe informar movimiento de cuenta
    corriente cancelado y comprobante asociado.
    """
    app = create_app(TestConfig)

    with app.app_context():
        cliente_id = _preparar_datos_base_en_contexto()

        with pytest.raises(ValueError, match="linea aplicada"):
            crear_cobranza_cliente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-06-17",
                    "tipo_cobranza": "APLICADA",
                    "total_centavos": 100000,
                },
                [
                    {
                        "tipo_linea": "FACTURA",
                        "importe_centavos": 100000,
                        "cuenta_cancelacion_codigo": "1.1.02.01.001",
                    }
                ],
            )
