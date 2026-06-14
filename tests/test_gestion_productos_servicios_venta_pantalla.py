from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.articulos_venta_service import crear_articulo_venta_desde_formulario


def test_routes_productos_servicios_venta_no_usan_sql_directo():
    """Valida que routes de gestion deleguen persistencia al service."""
    contenido = Path("app/gestion/routes.py").read_text(encoding="utf-8")

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_pantalla_productos_servicios_venta_responde_ok_sin_datos():
    """Valida listado de productos o servicios para la venta sin datos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/productos-servicios-venta/")

    assert response.status_code == 200
    assert b"Productos o servicios para la venta" in response.data
    assert b"No hay productos o servicios para la venta cargados." in response.data
    assert b'id="psv-listado"' in response.data
    assert b'id="psv-tabla"' in response.data
    assert b'data-table="articulos_venta"' in response.data
    assert b"Nuevo producto o servicio" in response.data


def test_pantalla_productos_servicios_venta_muestra_datos():
    """Valida que el listado muestre productos o servicios cargados por service."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio pantalla",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "precio_unitario_sugerido_centavos": "1,00",
                "activo": "1",
                "orden": "10",
                "observaciones": "Visible en listado.",
            }
        )

        response = client.get("/gestion/productos-servicios-venta/")

    assert response.status_code == 200
    assert b"Servicio pantalla" in response.data
    assert b"Servicio" in response.data
    assert b"ARS" in response.data
    assert b"1,00" in response.data
    assert b"Visible en listado." in response.data
    assert b"Editar" in response.data
    assert b"Desactivar" in response.data


def test_formulario_nuevo_producto_servicio_venta_responde_ok():
    """Valida formulario de alta manual con selects normales."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/productos-servicios-venta/nuevo/")

    assert response.status_code == 200
    assert b"Nuevo producto o servicio para la venta" in response.data
    assert b'id="psv-form"' in response.data
    assert b'id="psv-nombre"' in response.data
    assert b'id="psv-tipo"' in response.data
    assert b'id="psv-moneda"' in response.data
    assert b'id="psv-precio-sugerido"' in response.data
    assert b'data-money-ar="centavos"' in response.data
    assert b'inputmode="decimal"' in response.data
    assert b'name="precio_unitario_sugerido_centavos"' in response.data
    assert b'id="psv-cuenta-ingreso"' in response.data
    assert b'data-ns-select="normal"' in response.data


def test_crear_producto_servicio_venta_nuevo_desde_pantalla():
    """Valida POST de alta manual sin SQL en route."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()

        response = client.post(
            "/gestion/productos-servicios-venta/nuevo/",
            data={
                "nombre": "Servicio post pantalla",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "precio_unitario_sugerido_centavos": "250,00",
                "activo": "1",
                "orden": "4",
                "observaciones": "Alta desde pantalla.",
            },
            follow_redirects=True,
        )

        articulo = db.execute(
            """
            SELECT nombre, tipo, moneda_codigo, precio_unitario_sugerido_centavos,
                   activo, orden, observaciones
            FROM articulos_venta
            WHERE nombre = ?
            """,
            ("Servicio post pantalla",),
        ).fetchone()

    assert response.status_code == 200
    assert articulo["nombre"] == "Servicio post pantalla"
    assert articulo["tipo"] == "SERVICIO"
    assert articulo["moneda_codigo"] == "ARS"
    assert articulo["precio_unitario_sugerido_centavos"] == 25000
    assert articulo["activo"] == 1
    assert articulo["orden"] == 4
    assert articulo["observaciones"] == "Alta desde pantalla."
    assert b"Servicio post pantalla" in response.data


def test_crear_producto_servicio_venta_rechaza_nombre_vacio():
    """Valida respuesta 400 cuando el service rechaza el formulario."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.post(
            "/gestion/productos-servicios-venta/nuevo/",
            data={
                "nombre": "   ",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": "1",
                "orden": "10",
            },
        )

    assert response.status_code == 400
    assert b"El nombre del producto o servicio es obligatorio." in response.data


def test_crear_producto_servicio_venta_rechaza_precio_entero_crudo():
    """Valida que el importe preserve el valor invalido al re-renderizar."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.post(
            "/gestion/productos-servicios-venta/nuevo/",
            data={
                "nombre": "Servicio precio crudo",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "precio_unitario_sugerido_centavos": "123456",
                "activo": "1",
            },
        )

    assert response.status_code == 400
    assert b"formato argentino" in response.data
    assert b'value="123456"' in response.data


def test_editar_producto_servicio_venta_desde_pantalla():
    """Valida GET y POST de edicion manual."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        articulo = crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio original pantalla",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": "1",
                "orden": "10",
            }
        )

        get_response = client.get(
            f"/gestion/productos-servicios-venta/{articulo['id']}/editar/"
        )
        post_response = client.post(
            f"/gestion/productos-servicios-venta/{articulo['id']}/editar/",
            data={
                "nombre": "Producto editado pantalla",
                "tipo": "PRODUCTO",
                "moneda_codigo": "USD",
                "precio_unitario_sugerido_centavos": "5,00",
                "activo": "1",
                "orden": "15",
                "observaciones": "Editado desde pantalla.",
            },
            follow_redirects=True,
        )

        actualizado = get_db().execute(
            """
            SELECT nombre, tipo, moneda_codigo, precio_unitario_sugerido_centavos,
                   orden, observaciones
            FROM articulos_venta
            WHERE id = ?
            """,
            (articulo["id"],),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar producto o servicio para la venta Servicio original pantalla" in get_response.data
    assert post_response.status_code == 200
    assert actualizado["nombre"] == "Producto editado pantalla"
    assert actualizado["tipo"] == "PRODUCTO"
    assert actualizado["moneda_codigo"] == "USD"
    assert actualizado["precio_unitario_sugerido_centavos"] == 500
    assert actualizado["orden"] == 15
    assert actualizado["observaciones"] == "Editado desde pantalla."


def test_activar_desactivar_producto_servicio_venta_desde_pantalla():
    """Valida POST de baja logica y reactivacion desde listado."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        articulo = crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio estado pantalla",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": "1",
                "orden": "10",
            }
        )

        desactivar_response = client.post(
            f"/gestion/productos-servicios-venta/{articulo['id']}/desactivar/",
            follow_redirects=True,
        )
        articulo_desactivado = get_db().execute(
            "SELECT activo FROM articulos_venta WHERE id = ?",
            (articulo["id"],),
        ).fetchone()

        activar_response = client.post(
            f"/gestion/productos-servicios-venta/{articulo['id']}/activar/",
            follow_redirects=True,
        )
        articulo_activado = get_db().execute(
            "SELECT activo FROM articulos_venta WHERE id = ?",
            (articulo["id"],),
        ).fetchone()

    assert desactivar_response.status_code == 200
    assert activar_response.status_code == 200
    assert articulo_desactivado["activo"] == 0
    assert articulo_activado["activo"] == 1



def test_template_precio_sugerido_no_usa_number_crudo():
    """Valida que precio sugerido use contrato visual de importes argentinos."""
    contenido = Path(
        "app/gestion/templates/gestion/productos_servicios_venta_form.html"
    ).read_text(encoding="utf-8")

    posicion = contenido.index('id="psv-precio-sugerido"')
    bloque = contenido[posicion : contenido.index("</div>", posicion)]

    assert 'data-money-ar="centavos"' in bloque
    assert 'type="text"' in bloque
    assert 'inputmode="decimal"' in bloque
    assert 'value="{{ articulo.precio_unitario_sugerido_argentina' in bloque
    assert 'type="number"' not in bloque

def test_productos_servicios_venta_no_menciona_compras_ni_reglas_futuras():
    """Valida que la pantalla no fije circuitos futuros."""
    rutas = Path("app/gestion/routes.py").read_text(encoding="utf-8")
    listado = Path(
        "app/gestion/templates/gestion/productos_servicios_venta.html"
    ).read_text(encoding="utf-8")
    formulario = Path(
        "app/gestion/templates/gestion/productos_servicios_venta_form.html"
    ).read_text(encoding="utf-8")

    contenido = "\n".join([rutas, listado, formulario]).lower()

    assert "productos o servicios para la compra" not in contenido
    assert "precio_cliente" not in contenido
    assert "ultimo_precio" not in contenido
    assert "arca" not in contenido
    assert "stock" not in contenido
