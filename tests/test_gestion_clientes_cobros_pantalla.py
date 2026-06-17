from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.clientes_cuenta_corriente_service import crear_movimiento_debe_cliente

CUENTA_CAJA = "1.1.01.01.911"
CUENTA_DEUDORES = "1.1.02.01.911"
CUENTA_ANTICIPO = "2.1.01.01.911"


def test_routes_cobros_cliente_no_usan_sql_directo():
    """Contrato: routes delega cobros al service, sin SQL directo."""
    contenido = Path("app/gestion/routes.py").read_text(encoding="utf-8")

    assert "crear_cobro_cliente_desde_formulario" in contenido
    assert "get_db" not in contenido
    assert ".execute(" not in contenido


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


def _crear_cliente(db) -> int:
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
            "Cliente cobro pantalla",
            grupo_id,
            CUENTA_DEUDORES,
            CUENTA_ANTICIPO,
            1,
            "2026-01-01 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _crear_ejercicio(db) -> int:
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
            "Ejercicio test cobro pantalla",
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


def _crear_medio_operativo(db) -> None:
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
            "Pesos pantalla",
            "EFECTIVO",
            CUENTA_CAJA,
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
            911,
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


def _preparar_base_cobro() -> dict:
    apply_migrations()
    db = get_db()

    _crear_ejercicio(db)
    _crear_cuenta(db, CUENTA_CAJA, "Caja pantalla", "DEBE", "PATRIMONIAL", 1)
    _crear_cuenta(db, CUENTA_DEUDORES, "Deudores pantalla", "DEBE", "PATRIMONIAL", 1)
    _crear_cuenta(db, CUENTA_ANTICIPO, "Anticipo pantalla", "HABER", "PATRIMONIAL", 0)
    _crear_medio_operativo(db)

    cliente_id = _crear_cliente(db)
    comprobante_id = _crear_factura_confirmada(db, cliente_id, 3500000)
    movimiento = crear_movimiento_debe_cliente(
        {
            "cliente_id": cliente_id,
            "fecha": "2026-06-10",
            "tipo_movimiento": "FACTURA",
            "descripcion": "FC C 0001-00000911",
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


def test_pantalla_cobro_cliente_muestra_comprobante_y_caja():
    """
    Contrato: la pantalla de cobro muestra imputacion y medio de caja en un
    formulario unico temporal.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        base = _preparar_base_cobro()
        response = client.get(f"/gestion/clientes/{base['cliente_id']}/cobros/nuevo/")

    assert response.status_code == 200
    assert b'data-form="cobro-cliente"' in response.data
    assert b'name="movimientos_ctacte_cancelados"' in response.data
    assert b'id="cl-cobro-caja"' in response.data
    assert b'name="medio_operativo_codigo"' in response.data
    assert b"Confirmar cobro" in response.data


def test_post_cobro_cliente_confirma_y_redirige_a_cuenta_corriente():
    """
    Contrato: el POST del formulario confirma cobranza, caja, asiento y cuenta
    corriente usando el service transaccional.
    """
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
                "medio_operativo_codigo": "1",
                "importe_caja": "35.000,00",
                "fecha_valor": "17/06/2026",
                "referencia": "EFECTIVO",
                "detalle": "Cobro pantalla",
                "observaciones": "Cobro desde pantalla",
            },
        )

        db = get_db()
        cobranza = db.execute(
            "SELECT id, estado, total_centavos, asiento_id FROM clientes_cobranzas"
        ).fetchone()
        movimiento_caja = db.execute(
            "SELECT id, estado, origen_tipo, origen_id, asiento_id FROM movimientos_caja"
        ).fetchone()
        movimiento_haber = db.execute(
            """
            SELECT tipo_movimiento, haber_centavos, origen_tipo, origen_id, asiento_id
            FROM clientes_cuenta_corriente_movimientos
            WHERE tipo_movimiento = 'COBRANZA'
            """
        ).fetchone()
        asiento = db.execute(
            "SELECT tipo, estado FROM asientos_contables WHERE id = ?",
            (cobranza["asiento_id"],),
        ).fetchone()

    assert response.status_code == 302
    assert f"/gestion/clientes/{base['cliente_id']}/cuenta-corriente/".encode() in response.headers["Location"].encode()
    assert cobranza["estado"] == "CONFIRMADO"
    assert cobranza["total_centavos"] == 3500000
    assert movimiento_caja["estado"] == "CONFIRMADO"
    assert movimiento_caja["origen_tipo"] == "CLIENTE_COBRANZA"
    assert movimiento_caja["origen_id"] == cobranza["id"]
    assert movimiento_caja["asiento_id"] == cobranza["asiento_id"]
    assert movimiento_haber["tipo_movimiento"] == "COBRANZA"
    assert movimiento_haber["haber_centavos"] == 3500000
    assert movimiento_haber["origen_tipo"] == "CLIENTE_COBRANZA"
    assert movimiento_haber["origen_id"] == cobranza["id"]
    assert movimiento_haber["asiento_id"] == cobranza["asiento_id"]
    assert asiento["tipo"] == "COBRANZA"
    assert asiento["estado"] == "CONFIRMADO"
