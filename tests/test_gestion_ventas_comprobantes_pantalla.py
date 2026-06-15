from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.ventas_comprobantes_service import (
    confirmar_comprobante_venta,
    crear_borrador_comprobante_venta,
)


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
    assert b'data-field="subtotal_centavos"' in response.data
    assert b'id="vc-confirmar"' in response.data
    assert b"Sin asiento" in response.data
    assert b'id="vc-detalle-cuenta-corriente"' in response.data
    assert b"Sin movimiento de cuenta corriente asociado." in response.data


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
    assert b"EJ2026-0000001" in response.data
    assert b'id="vc-detalle-cuenta-corriente"' in response.data
    assert b'id="vc-cuenta-corriente-movimiento"' in response.data
    assert b"VENTA_COMPROBANTE" in response.data
    assert b"(ID " in response.data
    assert b'id="vc-confirmar"' not in response.data


def test_listado_venta_confirmada_muestra_numero_contable_de_asiento():
    """
    Valida que el listado de ventas muestre numero contable de asiento.

    El asiento_id es trazabilidad tecnica; la pantalla principal debe mostrar el
    numero_asiento confirmado para lectura contable.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_ejercicio(db)
        comprobante = _crear_comprobante_borrador(db)

        client.post(
            f"/gestion/ventas/comprobantes/{comprobante['id']}/confirmar/",
            follow_redirects=True,
        )

        response = client.get("/gestion/ventas/comprobantes/")

    assert response.status_code == 200
    assert b"CONFIRMADO" in response.data
    assert b"EJ2026-0000001" in response.data
    assert b"(ID " in response.data


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


def test_formulario_nuevo_comprobante_venta_responde_ok():
    """Valida pantalla de alta minima de comprobante de venta."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
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
        _crear_cliente(db)
        _crear_articulo_venta(db)

        response = client.get("/gestion/ventas/comprobantes/nuevo/")

    assert response.status_code == 200
    assert b"Nuevo comprobante de venta" in response.data
    assert b'id="vc-form"' in response.data
    assert b'id="vc-cliente"' in response.data
    assert b'id="vc-articulo"' in response.data
    assert b'id="vc-cantidad"' in response.data
    assert b'id="vc-unidad-medida"' in response.data
    assert b'id="vc-precio-unitario"' in response.data
    assert b'id="vc-tipo-bonificacion"' in response.data
    assert b'id="vc-bonificacion-valor"' in response.data
    assert b'id="vc-importe-bonificacion"' not in response.data
    assert b'id="vc-subtotal-linea"' in response.data
    assert b'id="vc-total-comprobante"' in response.data
    assert b'id="vc-punto-venta"' in response.data
    assert b'id="vc-numero"' in response.data
    assert b'value="1"' in response.data
    assert b'name="tipo_comprobante"' in response.data
    assert b'id="vc-comprobante-asociado-contenedor"' in response.data
    assert b'id="vc-comprobante-asociado"' in response.data
    assert b'name="comprobante_asociado_id"' in response.data
    assert b'id="vc-letra"' in response.data
    assert b'readonly' in response.data
    assert b"Cliente pantalla venta" in response.data
    assert b'data-lookup="ventas-articulos-activos"' in response.data
    assert b"Confirmar comprobante" in response.data


def test_formulario_nuevo_comprobante_venta_lista_fc_confirmadas_para_asociar():
    """Valida que el formulario tenga FC confirmadas disponibles para ND/NC."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_ejercicio(db)
        comprobante = _crear_comprobante_borrador(db)
        confirmar_comprobante_venta(comprobante["id"])

        response = client.get("/gestion/ventas/comprobantes/nuevo/")

    assert response.status_code == 200
    assert b'id="vc-comprobante-asociado"' in response.data
    assert f'data-cliente-id="{comprobante["cliente_id"]}"'.encode() in response.data
    assert comprobante["numero_formateado"].encode() in response.data
    assert b"FC C " in response.data


def test_listado_ventas_comprobantes_muestra_boton_nuevo():
    """Valida acceso desde listado al alta minima."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/ventas/comprobantes/")

    assert response.status_code == 200
    assert b"Nuevo comprobante" in response.data
    assert b"/gestion/ventas/comprobantes/nuevo/" in response.data


def test_confirmar_comprobante_venta_desde_formulario_nuevo():
    """Valida POST de alta: confirma comprobante y genera impactos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_ejercicio(db)
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
        cliente_id = _crear_cliente(db)
        articulo_id = _crear_articulo_venta(db)

        response = client.post(
            "/gestion/ventas/comprobantes/nuevo/",
            data={
                "cliente_id": str(cliente_id),
                "fecha": "2026-01-15",
                "fecha_vencimiento": "2026-02-15",
                "tipo_comprobante": "FACTURA",
                "letra": "X",
                "punto_venta": "99",
                "numero": "26",
                "moneda_codigo": "ARS",
                "articulo_venta_id": str(articulo_id),
                "cantidad": "1,00",
                "unidad_medida_codigo": "7",
                "precio_unitario_centavos": "1.500,00",
                "tipo_bonificacion_codigo": "2",
                "bonificacion_valor": "100,00",
                "observaciones": "Alta minima.",
            },
            follow_redirects=True,
        )

        comprobante = db.execute(
            """
            SELECT id, estado, descuento_centavos, total_centavos, asiento_id
            FROM ventas_comprobantes
            WHERE numero = ?
            """,
            (1,),
        ).fetchone()

        asiento = db.execute(
            """
            SELECT id, estado, numero_asiento
            FROM asientos_contables
            WHERE id = ?
            """,
            (comprobante["asiento_id"],),
        ).fetchone()

        movimiento = db.execute(
            """
            SELECT id, estado, tipo_movimiento, origen_tipo, origen_id, asiento_id
            FROM clientes_cuenta_corriente_movimientos
            WHERE origen_tipo = 'VENTA_COMPROBANTE'
              AND origen_id = ?
            """,
            (comprobante["id"],),
        ).fetchone()

        cantidad_movimientos = db.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM clientes_cuenta_corriente_movimientos
            WHERE origen_tipo = 'VENTA_COMPROBANTE'
              AND origen_id = ?
            """,
            (comprobante["id"],),
        ).fetchone()["cantidad"]

    assert response.status_code == 200
    assert b"Comprobante de venta confirmado correctamente." in response.data
    assert b"Servicio pantalla venta" in response.data
    assert b"Monto" in response.data
    assert b"100,00" in response.data
    assert b"1.500,00" in response.data
    assert b"CONFIRMADO" in response.data

    assert comprobante["estado"] == "CONFIRMADO"
    assert comprobante["descuento_centavos"] == 10000
    assert comprobante["total_centavos"] == 140000
    assert comprobante["asiento_id"] is not None

    assert asiento is not None
    assert asiento["estado"] == "CONFIRMADO"
    assert asiento["numero_asiento"] == 1

    assert movimiento is not None
    assert movimiento["estado"] == "CONFIRMADO"
    assert movimiento["tipo_movimiento"] == "FACTURA"
    assert movimiento["origen_tipo"] == "VENTA_COMPROBANTE"
    assert movimiento["origen_id"] == comprobante["id"]
    assert movimiento["asiento_id"] == asiento["id"]
    assert cantidad_movimientos == 1

    assert b"Sin asiento" not in response.data
    assert b"EJ2026-0000001" in response.data


def test_confirmar_nota_debito_desde_formulario_nuevo_guarda_asociacion_fc():
    """Valida que ND desde pantalla guarde la FC asociada y confirme."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_ejercicio(db)
        fc = _crear_comprobante_borrador(db)
        fc_confirmada = confirmar_comprobante_venta(fc["id"])["comprobante"]

        articulo = db.execute(
            """
            SELECT id
            FROM articulos_venta
            WHERE nombre = ?
            ORDER BY id
            LIMIT 1
            """,
            ("Servicio pantalla venta",),
        ).fetchone()

        response = client.post(
            "/gestion/ventas/comprobantes/nuevo/",
            data={
                "cliente_id": str(fc_confirmada["cliente_id"]),
                "fecha": "2026-01-16",
                "fecha_vencimiento": "2026-02-16",
                "tipo_comprobante": "012",
                "comprobante_asociado_id": str(fc_confirmada["id"]),
                "letra": "C",
                "punto_venta": "1",
                "numero": "99",
                "moneda_codigo": "ARS",
                "articulo_venta_id": str(articulo["id"]),
                "cantidad": "1,00",
                "unidad_medida_codigo": "7",
                "precio_unitario_centavos": "500,00",
                "tipo_bonificacion_codigo": "",
                "bonificacion_valor": "0,00",
                "observaciones": "ND asociada a FC.",
            },
            follow_redirects=True,
        )

        nd = db.execute(
            """
            SELECT id, estado, tipo_comprobante, total_centavos, asiento_id
            FROM ventas_comprobantes
            WHERE tipo_comprobante = 'NOTA_DEBITO'
            LIMIT 1
            """
        ).fetchone()

        asociacion = db.execute(
            """
            SELECT comprobante_id, comprobante_asociado_id, tipo_relacion
            FROM ventas_comprobantes_asociaciones
            WHERE comprobante_id = ?
            """,
            (nd["id"],),
        ).fetchone()

        movimiento = db.execute(
            """
            SELECT tipo_movimiento, debe_centavos, haber_centavos
            FROM clientes_cuenta_corriente_movimientos
            WHERE origen_tipo = 'VENTA_COMPROBANTE'
              AND origen_id = ?
            """,
            (nd["id"],),
        ).fetchone()

    assert response.status_code == 200
    assert b"Comprobante de venta confirmado correctamente." in response.data
    assert b"ND C " in response.data
    assert b"Modifica a" in response.data
    assert fc_confirmada["numero_formateado"].encode() in response.data

    assert nd["estado"] == "CONFIRMADO"
    assert nd["tipo_comprobante"] == "NOTA_DEBITO"
    assert nd["total_centavos"] == 50000
    assert nd["asiento_id"] is not None

    assert asociacion["comprobante_id"] == nd["id"]
    assert asociacion["comprobante_asociado_id"] == fc_confirmada["id"]
    assert asociacion["tipo_relacion"] == "MODIFICA"

    assert movimiento["tipo_movimiento"] == "NOTA_DEBITO"
    assert movimiento["debe_centavos"] == 50000
    assert movimiento["haber_centavos"] == 0


def test_confirmar_nota_credito_desde_formulario_rechaza_sin_fc_asociada():
    """Valida que NC no pueda confirmarse desde pantalla sin FC asociada."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_ejercicio(db)
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
        cliente_id = _crear_cliente(db)
        articulo_id = _crear_articulo_venta(db)

        response = client.post(
            "/gestion/ventas/comprobantes/nuevo/",
            data={
                "cliente_id": str(cliente_id),
                "fecha": "2026-01-16",
                "fecha_vencimiento": "2026-02-16",
                "tipo_comprobante": "013",
                "comprobante_asociado_id": "",
                "letra": "C",
                "punto_venta": "1",
                "numero": "99",
                "moneda_codigo": "ARS",
                "articulo_venta_id": str(articulo_id),
                "cantidad": "1,00",
                "unidad_medida_codigo": "7",
                "precio_unitario_centavos": "500,00",
                "tipo_bonificacion_codigo": "",
                "bonificacion_valor": "0,00",
            },
            follow_redirects=False,
        )

        cantidad_nc = db.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM ventas_comprobantes
            WHERE tipo_comprobante = 'NOTA_CREDITO'
            """
        ).fetchone()["cantidad"]

    assert response.status_code == 400
    assert b"FC asociada" in response.data
    assert cantidad_nc == 0


def test_post_nuevo_comprobante_no_deja_borrador_si_falla_confirmacion():
    """
    Contrato: el POST real de nuevo comprobante es transaccional.

    Si el usuario carga datos y al confirmar falla la generacion de impactos,
    no debe quedar una venta BORRADOR huerfana.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_ejercicio(db)
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
        cliente_id = _crear_cliente(db, cuenta_deudores=None)
        articulo_id = _crear_articulo_venta(db)

        response = client.post(
            "/gestion/ventas/comprobantes/nuevo/",
            data={
                "cliente_id": str(cliente_id),
                "fecha": "2026-01-15",
                "fecha_vencimiento": "2026-02-15",
                "tipo_comprobante": "FACTURA",
                "letra": "X",
                "punto_venta": "99",
                "numero": "26",
                "moneda_codigo": "ARS",
                "articulo_venta_id": str(articulo_id),
                "cantidad": "1,00",
                "unidad_medida_codigo": "7",
                "precio_unitario_centavos": "1.500,00",
                "observaciones": "Alta que debe fallar al confirmar.",
            },
            follow_redirects=True,
        )

        cantidad_comprobantes = db.execute(
            "SELECT COUNT(*) AS cantidad FROM ventas_comprobantes"
        ).fetchone()["cantidad"]
        cantidad_asientos = db.execute(
            "SELECT COUNT(*) AS cantidad FROM asientos_contables"
        ).fetchone()["cantidad"]
        cantidad_movimientos = db.execute(
            "SELECT COUNT(*) AS cantidad FROM clientes_cuenta_corriente_movimientos"
        ).fetchone()["cantidad"]

    assert response.status_code == 400
    assert b"deudores" in response.data
    assert cantidad_comprobantes == 0
    assert cantidad_asientos == 0
    assert cantidad_movimientos == 0


def test_crear_borrador_comprobante_venta_desde_pantalla_rechaza_cliente_vacio():
    """Valida re-render 400 cuando falta cliente."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_cuenta_contable(
            db,
            CUENTA_INGRESO,
            "Ingresos por servicios pantalla",
            "HABER",
            "RESULTADO",
            0,
        )
        articulo_id = _crear_articulo_venta(db)

        response = client.post(
            "/gestion/ventas/comprobantes/nuevo/",
            data={
                "cliente_id": "",
                "fecha": "2026-01-15",
                "tipo_comprobante": "FACTURA",
                "letra": "X",
                "punto_venta": "1",
                "numero": "27",
                "moneda_codigo": "ARS",
                "articulo_venta_id": str(articulo_id),
                "cantidad": "1,00",
            },
        )

    assert response.status_code == 400
    assert b"El cliente es obligatorio." in response.data
    assert b'id="vc-form"' in response.data


def test_crear_borrador_comprobante_venta_desde_pantalla_rechaza_precio_invalido():
    """Valida formato argentino para precio unitario manual."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
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
        cliente_id = _crear_cliente(db)
        articulo_id = _crear_articulo_venta(db)

        response = client.post(
            "/gestion/ventas/comprobantes/nuevo/",
            data={
                "cliente_id": str(cliente_id),
                "fecha": "2026-01-15",
                "tipo_comprobante": "FACTURA",
                "letra": "X",
                "punto_venta": "1",
                "numero": "28",
                "moneda_codigo": "ARS",
                "articulo_venta_id": str(articulo_id),
                "cantidad": "1,00",
                "precio_unitario_centavos": "123456",
            },
        )

    assert response.status_code == 400
    assert b"formato argentino" in response.data
    assert b'value="123456"' in response.data

def test_formulario_nuevo_comprobante_venta_ubica_renglon_debajo_de_cabecera():
    """Valida layout: el renglon se carga debajo de cabecera sin cambiar contrato funcional."""
    contenido = Path("app/gestion/templates/gestion/ventas_comprobantes_form.html").read_text(
        encoding="utf-8"
    )

    assert 'id="vc-cabecera" class="col-12"' in contenido
    assert 'id="vc-renglon" class="col-12"' in contenido
    assert 'id="vc-renglon-scroll" class="table-responsive"' in contenido
    assert 'id="vc-punto-venta" name="punto_venta" type="number" min="1" step="1" class="form-control text-end" value="{{ comprobante_form.punto_venta }}" readonly required' in contenido
    assert 'id="vc-numero" name="numero" type="number" min="1" step="1" class="form-control text-end" value="{{ comprobante_form.numero }}" readonly required' in contenido
    assert 'id="vc-renglon-tabla"' in contenido
    assert 'class="table table-sm table-hover align-middle mb-2 vc-renglon-tabla"' in contenido
    assert 'id="vc-renglon-minimo" data-role="venta-renglones"' in contenido
    assert 'data-role="venta-renglon"' in contenido
    assert "<thead>" in contenido
    assert 'id="vc-articulo"' in contenido
    assert 'data-lookup="ventas-articulos-activos"' in contenido
    assert 'data-lookup-url="{{ url_for(\'gestion.buscar_productos_servicios_venta_json\') }}"' in contenido
    assert 'data-lookup-hidden="vc-articulo-id"' in contenido
    assert 'id="vc-articulo-id"' in contenido
    assert 'name="articulo_venta_id"' in contenido
    assert 'id="vc-articulo-opciones"' in contenido
    assert 'data-field="articulo_venta_lookup_opciones"' in contenido
    assert 'name="articulo_venta_id" class="form-select form-select-sm"' not in contenido
    assert 'id="vc-subtotal-linea"' in contenido
    assert 'id="vc-total-comprobante"' in contenido
    assert "Total comprobante" in contenido
    assert 'id="vc-unidad-medida" name="unidad_medida_codigo" class="visually-hidden"' in contenido
    assert 'id="vc-unidad-medida-badge"' in contenido
    assert 'data-badge="{{ unidad_badge }}"' in contenido
    assert 'id="vc-tipo-bonificacion" name="tipo_bonificacion_codigo" class="visually-hidden"' in contenido
    assert 'id="vc-tipo-bonificacion-badge"' in contenido
    assert 'value="" data-badge="Sin"' in contenido
    assert 'id="vc-importe-bonificacion"' not in contenido
    assert 'id="vc-descripcion-renglon"' not in contenido
    assert "Descripción opcional" not in contenido
    assert "ventas_comprobantes_form.css" in contenido
    assert "ventas_comprobantes_form.js" in contenido
    assert contenido.index('id="vc-cabecera"') < contenido.index('id="vc-renglon"')
    assert 'id="vc-cabecera" class="col-12 col-lg-7"' not in contenido
    assert 'id="vc-renglon" class="col-12 col-lg-5"' not in contenido


def test_css_formulario_ventas_comprobantes_mantiene_renglon_en_linea():
    """Valida contrato CSS para que el renglon use tabla horizontal compacta."""
    contenido = Path("app/static/css/ventas_comprobantes_form.css").read_text(
        encoding="utf-8"
    )

    assert ".vc-renglon-tabla" in contenido
    assert "table-layout: fixed" in contenido
    assert "min-width: 1060px" in contenido
    assert ".vc-renglon-badge" in contenido
    assert ".vc-renglon-badge--unidad" in contenido
    assert ".vc-renglon-badge--porcentaje" in contenido
    assert ".vc-renglon-badge--monto" in contenido
    assert ".vc-total-comprobante" in contenido
    assert ".vc-renglon-descripcion" not in contenido


def test_js_formulario_ventas_comprobantes_calcula_subtotal_linea():
    """Valida contrato JS de subtotal de renglon y bonificacion calculada."""
    contenido = Path("app/static/js/ventas_comprobantes_form.js").read_text(
        encoding="utf-8"
    )

    assert "SELECTORES" in contenido
    assert "vc-subtotal-linea" in contenido
    assert "vc-total-comprobante" in contenido
    assert "calcularBonificacionCentavos" in contenido
    assert "actualizarSubtotalLinea" in contenido
    assert "ventas-articulos-activos" in contenido
    assert "cargarOpcionesLookupArticulos" in contenido
    assert "sincronizarArticuloSeleccionado" in contenido
    assert "ciclarBadge" in contenido
    assert "sincronizarBadge" in contenido
    assert "decimalArAEnteroEscala" in contenido


def test_formulario_nuevo_comprobante_venta_autonumera_pv_1():
    """Valida que alta de pantalla muestre PV 1 y proximo numero readonly."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
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
        cliente_id = _crear_cliente(db)
        articulo_id = _crear_articulo_venta(db)

        crear_borrador_comprobante_venta(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-15",
                "tipo_comprobante": "FACTURA",
                "letra": "X",
                "punto_venta": "1",
                "numero": "1",
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

        response = client.get("/gestion/ventas/comprobantes/nuevo/")

    assert response.status_code == 200
    assert b'id="vc-punto-venta"' in response.data
    assert b'value="1"' in response.data
    assert b'id="vc-numero"' in response.data
    assert b'value="2"' in response.data


def test_lookup_productos_servicios_venta_devuelve_json():
    """Valida endpoint JSON de lookup para renglones de comprobantes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_cuenta_contable(
            db,
            CUENTA_INGRESO,
            "Ingresos por servicios pantalla",
            "HABER",
            "RESULTADO",
            0,
        )
        _crear_articulo_venta(db)

        response = client.get(
            "/gestion/productos-servicios-venta/buscar/?q=Servicio&limite=10"
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["cantidad"] == 1
    assert payload["resultados"][0]["label"] == "Servicio pantalla venta - ARS"
    assert payload["resultados"][0]["valor"]

