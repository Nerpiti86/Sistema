from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.ventas_comprobantes_service import crear_borrador_comprobante_venta


CUENTA_DEUDORES = "1.1.03.01.995"
CUENTA_INGRESO = "4.1.01.01.995"


def test_routes_ventas_comprobantes_no_usan_sql_directo():
    """Valida que routes de gestion deleguen comprobantes de venta al service."""
    contenido = Path("app/gestion/routes.py").read_text(encoding="utf-8")

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def _crear_grupo_cliente(db) -> int:
    fila_grupo = db.execute(
        """
        SELECT id
        FROM grupos_clientes
        WHERE nombre = ?
        LIMIT 1
        """,
        ("General",),
    ).fetchone()

    if fila_grupo is not None:
        return int(fila_grupo["id"])

    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("General", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cuenta_contable(
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
            sumarizadora,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            1,
            monetaria,
            None,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def _crear_cliente(db, cuenta_deudores: str | None = CUENTA_DEUDORES) -> int:
    grupo_id = _crear_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (
            razon_social,
            grupo_cliente_id,
            cuenta_deudores_ventas_codigo,
            activo,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "Cliente pantalla venta",
            grupo_id,
            cuenta_deudores,
            1,
            "2026-01-01 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _crear_articulo_venta(db, cuenta_ingreso: str = CUENTA_INGRESO) -> int:
    cursor = db.execute(
        """
        INSERT INTO articulos_venta (
            nombre,
            tipo,
            moneda_codigo,
            precio_unitario_sugerido_centavos,
            cuenta_ingreso_codigo,
            activo,
            orden,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Servicio pantalla venta",
            "SERVICIO",
            "ARS",
            100000,
            cuenta_ingreso,
            1,
            10,
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
        ORDER BY id
        LIMIT 1
        """,
        ("2026-01-15", "2026-01-15"),
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
            "Ejercicio test pantalla venta",
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


def _crear_comprobante_borrador(db, *, cuenta_deudores=CUENTA_DEUDORES) -> dict:
    _crear_cuenta_contable(
        db,
        CUENTA_DEUDORES,
        "Deudores por ventas pantalla",
        "DEBE",
        "PATRIMONIAL",
        1,
    )
    _crear_cuenta_contable(
        db,
        CUENTA_INGRESO,
        "Ingresos por servicios pantalla",
        "HABER",
        "RESULTADO",
        0,
    )
    cliente_id = _crear_cliente(db, cuenta_deudores)
    articulo_id = _crear_articulo_venta(db)

    return crear_borrador_comprobante_venta(
        {
            "cliente_id": cliente_id,
            "fecha": "2026-01-15",
            "fecha_vencimiento": "2026-02-15",
            "tipo_comprobante": "FACTURA",
            "letra": "X",
            "punto_venta": "1",
            "numero": "25",
            "moneda_codigo": "ARS",
            "cotizacion_centavos": "100",
        },
        [
            {
                "articulo_venta_id": articulo_id,
                "cantidad_1000000": "1000000",
                "iva_centavos": "0",
            }
        ],
    )


def test_pantalla_ventas_comprobantes_responde_ok_sin_datos():
    """Valida listado de comprobantes de venta sin datos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/ventas/comprobantes/")

    assert response.status_code == 200
    assert b"Comprobantes de venta" in response.data
    assert b"No hay comprobantes de venta cargados." in response.data
    assert b'id="vc-listado"' in response.data
    assert b'id="vc-tabla"' in response.data
    assert b'data-table="ventas_comprobantes"' in response.data


def test_pantalla_ventas_comprobantes_muestra_borrador():
    """Valida que el listado muestre un comprobante borrador existente."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        comprobante = _crear_comprobante_borrador(get_db())
        response = client.get("/gestion/ventas/comprobantes/")

    assert response.status_code == 200
    assert f'vc-row-{comprobante["id"]}'.encode() in response.data
    assert b"Cliente pantalla venta" in response.data
    assert b"FACTURA" in response.data
    assert b"BORRADOR" in response.data
    assert b"1.000,00" in response.data
    assert b"Ver detalle" in response.data


def test_pantalla_detalle_venta_muestra_cabecera_y_renglones():
    """Valida detalle de comprobante de venta con renglones."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        comprobante = _crear_comprobante_borrador(get_db())
        response = client.get(f"/gestion/ventas/comprobantes/{comprobante['id']}/")

    assert response.status_code == 200
    assert b"Detalle comprobante de venta" in response.data
    assert b"Cliente pantalla venta" in response.data
    assert b"Servicio pantalla venta" in response.data
    assert b"1.000,00" in response.data
    assert b'id="vc-confirmar"' in response.data
    assert b"Sin asiento" in response.data


def test_confirmar_venta_desde_pantalla():
    """Valida POST de confirmacion desde pantalla."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_ejercicio(db)
        comprobante = _crear_comprobante_borrador(db)

        response = client.post(
            f"/gestion/ventas/comprobantes/{comprobante['id']}/confirmar/",
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"Comprobante de venta confirmado correctamente." in response.data
    assert b"CONFIRMADO" in response.data
    assert b"Sin asiento" not in response.data
    assert b'id="vc-confirmar"' not in response.data


def test_confirmar_venta_desde_pantalla_muestra_error_funcional():
    """Valida que un error funcional vuelva al detalle sin confirmar."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_ejercicio(db)
        comprobante = _crear_comprobante_borrador(db, cuenta_deudores=None)

        response = client.post(
            f"/gestion/ventas/comprobantes/{comprobante['id']}/confirmar/",
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"deudores" in response.data
    assert b"BORRADOR" in response.data
    assert b'id="vc-confirmar"' in response.data
