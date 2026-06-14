from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.clientes_service import crear_cliente_desde_formulario
from app.gestion.grupos_clientes_repository import crear_grupo_cliente


def _crear_grupo_cliente_activo(nombre="General"):
    return crear_grupo_cliente({"nombre": nombre, "activo": 1, "orden": 10})


def _crear_pais(db) -> int:
    cursor = db.execute(
        """
        INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Argentina", "AR", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_provincia(db, pais_id: int) -> int:
    cursor = db.execute(
        """
        INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?, ?)
        """,
        (pais_id, "Santa Fe", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def test_routes_gestion_clientes_no_usan_sql_directo():
    """Valida que routes de gestion deleguen persistencia al service."""
    contenido = Path("app/gestion/routes.py").read_text(encoding="utf-8")

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_pantalla_gestion_clientes_responde_ok_sin_datos():
    """
    Valida pantalla de clientes bajo Gestion.

    La route usa service y el template mantiene IDs cortos y data-* para
    trazabilidad tecnica de tabla, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/clientes/")

    assert response.status_code == 200
    assert b"Clientes" in response.data
    assert b"No hay clientes cargados." in response.data
    assert b'id="cl-listado"' in response.data
    assert b'id="cl-tabla"' in response.data
    assert b'data-table="clientes"' in response.data
    assert b'data-query="listar_clientes"' in response.data
    assert b"Nuevo cliente" in response.data


def test_pantalla_gestion_clientes_muestra_datos():
    """Valida que el listado muestre clientes cargados por service."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        grupo = _crear_grupo_cliente_activo()
        crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Uno SA",
                "nombre_fantasia": "Uno Comercial",
                "grupo_cliente_id": str(grupo["id"]),
                "tipo_documento_fiscal_codigo": "80",
                "numero_documento_fiscal": "30700000001",
                "activo": "1",
                "orden": "10",
            }
        )
        response = client.get("/gestion/clientes/")

    assert response.status_code == 200
    assert b"Cliente Uno SA" in response.data
    assert b"Uno Comercial" in response.data
    assert b"CUIT 30700000001" in response.data
    assert b"Editar" in response.data
    assert b"Desactivar" in response.data


def test_navbar_tiene_gestion_clientes():
    """Valida acceso de navegacion Gestion > Clientes > Clientes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/clientes/")

    assert response.status_code == 200
    assert b"/gestion/clientes/" in response.data
    assert b'id="ns-nav-gestion"' in response.data
    assert b'id="ns-nav-clientes-maestro"' in response.data
    assert b'id="ns-nav-grupos-clientes"' in response.data


def test_formulario_nuevo_cliente_responde_ok():
    """Valida formulario de alta manual de clientes con selects normales."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_grupo_cliente_activo()
        response = client.get("/gestion/clientes/nuevo/")

    assert response.status_code == 200
    assert b"Nuevo cliente" in response.data
    assert b'id="cl-form"' in response.data
    assert b'id="cl-razon-social"' in response.data
    assert b'id="cl-grupo-cliente"' in response.data
    assert b'id="cl-condicion-iva"' in response.data
    assert b'id="cl-tipo-documento-fiscal"' in response.data
    assert b'id="cl-cuenta-deudores-ventas"' in response.data
    assert b'data-ns-select="normal"' in response.data


def test_formulario_nuevo_cliente_avisa_si_no_hay_grupos_activos():
    """Valida alerta operativa cuando no existen grupos activos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/clientes/nuevo/")

    assert response.status_code == 200
    assert b'id="cl-alerta-sin-grupos"' in response.data
    assert b"primero debe existir al menos un grupo" in response.data


def test_crear_cliente_nuevo_desde_pantalla():
    """Valida POST de alta manual sin SQL en route."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo = _crear_grupo_cliente_activo()
        pais_id = _crear_pais(db)
        provincia_id = _crear_provincia(db, pais_id)

        response = client.post(
            "/gestion/clientes/nuevo/",
            data={
                "razon_social": "Cliente Pantalla SA",
                "nombre_fantasia": "Pantalla Comercial",
                "grupo_cliente_id": str(grupo["id"]),
                "telefono": "3410000000",
                "email": "cliente@example.com",
                "domicilio": "Calle 123",
                "codigo_postal": "S2000",
                "ciudad": "Rosario",
                "pais_id": str(pais_id),
                "provincia_id": str(provincia_id),
                "condicion_iva_codigo": "5",
                "tipo_documento_fiscal_codigo": "80",
                "numero_documento_fiscal": "30700000001",
                "activo": "1",
                "orden": "10",
            },
            follow_redirects=True,
        )
        cliente = db.execute(
            """
            SELECT razon_social, nombre_fantasia, activo, orden
            FROM clientes
            WHERE razon_social = ?
            """,
            ("Cliente Pantalla SA",),
        ).fetchone()

    assert response.status_code == 200
    assert cliente["razon_social"] == "Cliente Pantalla SA"
    assert cliente["nombre_fantasia"] == "Pantalla Comercial"
    assert cliente["activo"] == 1
    assert cliente["orden"] == 10
    assert b"Cliente Pantalla SA" in response.data


def test_crear_cliente_nuevo_rechaza_razon_social_vacia():
    """Valida respuesta 400 cuando el service rechaza el formulario."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        grupo = _crear_grupo_cliente_activo()
        response = client.post(
            "/gestion/clientes/nuevo/",
            data={
                "razon_social": "   ",
                "grupo_cliente_id": str(grupo["id"]),
                "activo": "1",
                "orden": "10",
            },
        )

    assert response.status_code == 400
    assert b"La razon social del cliente es obligatoria." in response.data


def test_editar_cliente_desde_pantalla():
    """Valida GET y POST de edicion manual de cliente."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        grupo = _crear_grupo_cliente_activo()
        cliente = crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Original",
                "grupo_cliente_id": str(grupo["id"]),
                "activo": "1",
                "orden": "10",
            }
        )

        get_response = client.get(f"/gestion/clientes/{cliente['id']}/editar/")
        post_response = client.post(
            f"/gestion/clientes/{cliente['id']}/editar/",
            data={
                "razon_social": "Cliente Editado",
                "nombre_fantasia": "Editado Comercial",
                "grupo_cliente_id": str(grupo["id"]),
                "telefono": "3410000000",
                "activo": "1",
                "orden": "15",
            },
            follow_redirects=True,
        )
        cliente_actualizado = get_db().execute(
            """
            SELECT razon_social, nombre_fantasia, telefono, orden
            FROM clientes
            WHERE id = ?
            """,
            (cliente["id"],),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar cliente Cliente Original" in get_response.data
    assert post_response.status_code == 200
    assert cliente_actualizado["razon_social"] == "Cliente Editado"
    assert cliente_actualizado["nombre_fantasia"] == "Editado Comercial"
    assert cliente_actualizado["telefono"] == "3410000000"
    assert cliente_actualizado["orden"] == 15


def test_activar_desactivar_cliente_desde_pantalla():
    """Valida POST de baja logica y reactivacion desde listado."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        grupo = _crear_grupo_cliente_activo()
        cliente = crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Estado",
                "grupo_cliente_id": str(grupo["id"]),
                "activo": "1",
                "orden": "10",
            }
        )

        desactivar_response = client.post(
            f"/gestion/clientes/{cliente['id']}/desactivar/",
            follow_redirects=True,
        )
        cliente_desactivado = get_db().execute(
            "SELECT activo FROM clientes WHERE id = ?",
            (cliente["id"],),
        ).fetchone()
        activar_response = client.post(
            f"/gestion/clientes/{cliente['id']}/activar/",
            follow_redirects=True,
        )
        cliente_activado = get_db().execute(
            "SELECT activo FROM clientes WHERE id = ?",
            (cliente["id"],),
        ).fetchone()

    assert desactivar_response.status_code == 200
    assert activar_response.status_code == 200
    assert cliente_desactivado["activo"] == 0
    assert cliente_activado["activo"] == 1


def test_template_clientes_no_define_cuenta_ingreso():
    """Valida que ingresos queden fuera de pantalla clientes."""
    listado = Path("app/gestion/templates/gestion/clientes.html").read_text(
        encoding="utf-8"
    )
    formulario = Path("app/gestion/templates/gestion/clientes_form.html").read_text(
        encoding="utf-8"
    )

    assert "cuenta_ingreso" not in listado
    assert "cuenta_ingreso" not in formulario


def test_formulario_cliente_tiene_tabs():
    """Valida estructura de tabs del formulario de clientes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_grupo_cliente_activo()
        response = client.get("/gestion/clientes/nuevo/")

    assert response.status_code == 200
    assert b'id="cl-datos-principales"' in response.data
    assert b'id="cl-tabs"' in response.data
    assert b'id="cl-tab-contacto"' in response.data
    assert b'id="cl-panel-contacto"' in response.data
    assert b'id="cl-tab-fiscal"' in response.data
    assert b'id="cl-panel-fiscal"' in response.data
    assert b'id="cl-tab-contable"' in response.data
    assert b'id="cl-panel-contable"' in response.data
    assert b"Contacto" in response.data
    assert b"Fiscal" in response.data
    assert "Conexión contable".encode("utf-8") in response.data


def test_formulario_nuevo_cliente_default_argentina_santa_fe():
    """Valida defaults geograficos Argentina y Santa Fe en alta."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_grupo_cliente_activo()
        pais_id = _crear_pais(db)
        provincia_id = _crear_provincia(db, pais_id)

        response = client.get("/gestion/clientes/nuevo/")

    assert response.status_code == 200
    assert f'value="{pais_id}" selected'.encode("utf-8") in response.data
    assert f'value="{provincia_id}" selected'.encode("utf-8") in response.data


def test_formulario_editar_cliente_no_pisa_geografia_vacia_con_default():
    """Valida que los defaults solo apliquen en alta, no en edicion."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo = _crear_grupo_cliente_activo()
        _crear_pais(db)
        cliente = crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Sin Geografia",
                "grupo_cliente_id": str(grupo["id"]),
                "activo": "1",
            }
        )

        response = client.get(f"/gestion/clientes/{cliente['id']}/editar/")

    assert response.status_code == 200
    assert b'id="cl-pais"' in response.data
    assert b'id="cl-provincia"' in response.data
    assert b'Seleccionar pa' in response.data
    assert b'Seleccionar provincia' in response.data

def test_formulario_cliente_respeta_orden_uiux_basico_y_contacto():
    """Valida contrato visual de orden de campos del formulario de clientes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_grupo_cliente_activo()
        response = client.get("/gestion/clientes/nuevo/")

    assert response.status_code == 200
    html = response.data.decode("utf-8")

    datos_principales = html.split('id="cl-datos-principales"', 1)[1].split('id="cl-tabs"', 1)[0]
    contacto = html.split('id="cl-panel-contacto"', 1)[1].split('id="cl-panel-fiscal"', 1)[0]

    assert datos_principales.index('id="cl-razon-social"') < datos_principales.index('id="cl-grupo-cliente"')
    assert datos_principales.index('id="cl-grupo-cliente"') < datos_principales.index('id="cl-nombre-fantasia"')
    assert datos_principales.index('id="cl-nombre-fantasia"') < datos_principales.index('id="cl-orden"')
    assert datos_principales.index('id="cl-orden"') < datos_principales.index('id="cl-activo"')

    assert "Nombre de fantasía" in datos_principales
    assert "Correo" in contacto

    assert contacto.index('id="cl-telefono"') < contacto.index('id="cl-email"')
    assert contacto.index('id="cl-email"') < contacto.index('id="cl-domicilio"')
    assert contacto.index('id="cl-domicilio"') < contacto.index('id="cl-ciudad"')
    assert contacto.index('id="cl-ciudad"') < contacto.index('id="cl-codigo-postal"')
    assert contacto.index('id="cl-codigo-postal"') < contacto.index('id="cl-pais"')
    assert contacto.index('id="cl-pais"') < contacto.index('id="cl-provincia"')

def test_formulario_cliente_tabs_en_panel_secundario():
    """Valida que los tabs del formulario queden contenidos en un panel visual secundario."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_grupo_cliente_activo()
        response = client.get("/gestion/clientes/nuevo/")

    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'id="cl-tabs-panel"' in html
    assert "border rounded-3 p-3 bg-body-tertiary" in html
    assert html.index('id="cl-datos-principales"') < html.index('id="cl-tabs-panel"')
    assert html.index('id="cl-tabs-panel"') < html.index('id="cl-tabs"')
    assert html.index('id="cl-tabs"') < html.index('id="cl-tabs-contenido"')
    assert html.index('id="cl-formulario"') < html.index('id="cl-datos-principales"')
    assert html.index('id="cl-formulario"') < html.index('id="cl-tabs-panel"')

