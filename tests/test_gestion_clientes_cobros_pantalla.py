from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.clientes_cuenta_corriente_service import crear_movimiento_debe_cliente

CUENTA_CAJA = "1.1.01.01.921"
CUENTA_DEUDORES = "1.1.02.01.921"
CUENTA_ANTICIPO = "2.1.01.01.921"


def _crear_cuenta(db, cuenta, descripcion, saldo_habitual, naturaleza, monetaria):
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


def _obtener_o_crear_grupo_cliente(db):
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


def _crear_cliente(db):
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
            "Cliente cobro caja transversal",
            grupo_id,
            CUENTA_DEUDORES,
            CUENTA_ANTICIPO,
            1,
            "2026-01-01 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _crear_ejercicio(db):
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
            "Ejercicio test caja transversal",
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


def _crear_medio_operativo(db):
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
            "Pesos caja transversal",
            "EFECTIVO",
            CUENTA_CAJA,
            "ARS",
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )


def _crear_factura_confirmada(db, cliente_id, total_centavos):
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
            921,
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


def _preparar_base_cobro():
    apply_migrations()
    db = get_db()

    _crear_ejercicio(db)
    _crear_cuenta(db, CUENTA_CAJA, "Caja transversal", "DEBE", "PATRIMONIAL", 1)
    _crear_cuenta(db, CUENTA_DEUDORES, "Deudores transversal", "DEBE", "PATRIMONIAL", 1)
    _crear_cuenta(db, CUENTA_ANTICIPO, "Anticipo transversal", "HABER", "PATRIMONIAL", 0)
    _crear_medio_operativo(db)

    cliente_id = _crear_cliente(db)
    comprobante_id = _crear_factura_confirmada(db, cliente_id, 3500000)
    movimiento = crear_movimiento_debe_cliente(
        {
            "cliente_id": cliente_id,
            "fecha": "2026-06-10",
            "tipo_movimiento": "FACTURA",
            "descripcion": "FC C 0001-00000921",
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
        "movimiento_id": movimiento["id"],
    }


def test_pantalla_cobro_cliente_crea_intencion_no_impacta_y_redirige_a_caja():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        base = _preparar_base_cobro()

        response = client.post(
            f"/gestion/clientes/{base['cliente_id']}/cobros/nuevo/",
            data={
                "cliente_id": str(base["cliente_id"]),
                "fecha": "17/06/2026",
                "tipo_comprobante": "RC",
                "letra": "C",
                "punto_venta": "1",
                "numero": "1",
                "moneda_codigo": "ARS",
                "movimientos_ctacte_cancelados": str(base["movimiento_id"]),
                f"venta_comprobante_id_{base['movimiento_id']}": str(base["comprobante_id"]),
                f"tipo_movimiento_{base['movimiento_id']}": "FACTURA",
                f"importe_a_cobrar_{base['movimiento_id']}": "35.000,00",
                "observaciones": "Intencion desde pantalla",
            },
        )

        db = get_db()
        intencion = db.execute("SELECT * FROM caja_intenciones").fetchone()
        cobranzas = db.execute("SELECT COUNT(*) AS cantidad FROM clientes_cobranzas").fetchone()

    assert response.status_code == 302
    assert "/caja/movimientos/nuevo/?intencion_id=".encode() in response.headers["Location"].encode()
    assert intencion["origen_tipo"] == "RECIBO_CLIENTE"
    assert intencion["tipo_movimiento"] == "INGRESO"
    assert intencion["total_esperado_centavos"] == 3500000
    assert intencion["estado"] == "PENDIENTE"
    assert cobranzas["cantidad"] == 0


def test_caja_transversal_confirma_intencion_recibo_cliente():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        base = _preparar_base_cobro()

        response_intencion = client.post(
            f"/gestion/clientes/{base['cliente_id']}/cobros/nuevo/",
            data={
                "cliente_id": str(base["cliente_id"]),
                "fecha": "17/06/2026",
                "tipo_comprobante": "RC",
                "letra": "C",
                "punto_venta": "1",
                "numero": "1",
                "moneda_codigo": "ARS",
                "movimientos_ctacte_cancelados": str(base["movimiento_id"]),
                f"venta_comprobante_id_{base['movimiento_id']}": str(base["comprobante_id"]),
                f"tipo_movimiento_{base['movimiento_id']}": "FACTURA",
                f"importe_a_cobrar_{base['movimiento_id']}": "35.000,00",
                "observaciones": "Intencion desde pantalla",
            },
        )

        db = get_db()
        intencion = db.execute("SELECT * FROM caja_intenciones").fetchone()

        response_caja_get = client.get(
            f"/caja/movimientos/nuevo/?intencion_id={intencion['id']}"
        )

        response_confirmar = client.post(
            "/caja/movimientos/nuevo/",
            data={
                "intencion_id": str(intencion["id"]),
                "tipo_movimiento": "INGRESO",
                "fecha": "17/06/2026",
                "lineas[0][medio_operativo_codigo]": "1",
                "lineas[0][medio_operativo_codigo_select]": "1",
                "lineas[0][fecha_valor]": "17/06/2026",
                "lineas[0][referencia]": "EFECTIVO",
                "lineas[0][importe]": "35.000,00",
                "lineas[0][detalle]": "Cobro caja transversal",
            },
        )

        intencion_confirmada = db.execute("SELECT * FROM caja_intenciones").fetchone()
        cobranza = db.execute("SELECT * FROM clientes_cobranzas").fetchone()
        movimiento_caja = db.execute("SELECT * FROM movimientos_caja").fetchone()
        movimiento_cc = db.execute(
            """
            SELECT *
            FROM clientes_cuenta_corriente_movimientos
            WHERE tipo_movimiento = 'COBRANZA'
            """
        ).fetchone()
        asiento = db.execute("SELECT * FROM asientos_contables WHERE id = ?", (cobranza["asiento_id"],)).fetchone()

    assert response_intencion.status_code == 302
    assert response_caja_get.status_code == 200
    assert b'data-form="movimiento-caja"' in response_caja_get.data
    assert b"RECIBO_CLIENTE" in response_caja_get.data
    assert response_confirmar.status_code == 302
    assert f"/gestion/clientes/{base['cliente_id']}/cuenta-corriente/".encode() in response_confirmar.headers["Location"].encode()

    assert intencion_confirmada["estado"] == "CONFIRMADA"
    assert intencion_confirmada["resultado_tipo"] == "CLIENTE_COBRANZA"
    assert intencion_confirmada["resultado_id"] == cobranza["id"]

    assert cobranza["estado"] == "CONFIRMADO"
    assert cobranza["total_centavos"] == 3500000
    assert movimiento_caja["estado"] == "CONFIRMADO"
    assert movimiento_caja["origen_tipo"] == "CLIENTE_COBRANZA"
    assert movimiento_caja["origen_id"] == cobranza["id"]
    assert movimiento_caja["asiento_id"] == cobranza["asiento_id"]
    assert movimiento_cc["haber_centavos"] == 3500000
    assert movimiento_cc["origen_tipo"] == "CLIENTE_COBRANZA"
    assert movimiento_cc["origen_id"] == cobranza["id"]
    assert asiento["tipo"] == "COBRANZA"
    assert asiento["estado"] == "CONFIRMADO"
