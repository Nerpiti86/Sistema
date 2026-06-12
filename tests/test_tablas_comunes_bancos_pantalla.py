from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_pantalla_tablas_comunes_bancos_responde_ok():
    """
    Valida pantalla de bancos bajo Tablas Comunes.

    La route usa service y el template mantiene IDs cortos y data-* para
    trazabilidad tecnica de tabla, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/bancos/")

    assert response.status_code == 200
    assert b"Bancos" in response.data
    assert b"285" in response.data
    assert b"BANCO MACRO S.A." in response.data
    assert b'id="ba-listado"' in response.data
    assert b'id="ba-tabla"' in response.data
    assert b'data-table="bancos"' in response.data
    assert b'data-query="listar_bancos"' in response.data
    assert b"Nuevo banco" in response.data
    assert b"Editar" in response.data
    assert b"Desactivar" in response.data


def test_pantalla_tablas_comunes_bancos_muestra_catalogo_inicial():
    """Valida que la pantalla muestre la carga inicial de bancos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/bancos/")

    assert response.status_code == 200
    assert b"BANCO DE GALICIA Y BUENOS AIRES S.A." in response.data
    assert b"BANCO MUNICIPAL DE ROSARIO" in response.data
    assert b"BANCO MACRO S.A." in response.data


def test_navbar_tiene_tablas_comunes_bancos():
    """Valida acceso de navegacion Tablas Comunes > Bancos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/bancos/")

    assert response.status_code == 200
    assert b"Tablas comunes" in response.data
    assert b"/tablas-comunes/bancos/" in response.data
    assert b'id="ns-nav-tablas-comunes"' in response.data
    assert b'id="ns-nav-bancos"' in response.data


def test_formulario_nuevo_banco_responde_ok():
    """Valida formulario de alta manual de bancos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/bancos/nuevo/")

    assert response.status_code == 200
    assert b"Nuevo banco" in response.data
    assert b'id="ba-form"' in response.data
    assert b'id="ba-codigo"' in response.data
    assert b'id="ba-nombre"' in response.data


def test_crear_banco_nuevo_desde_pantalla():
    """Valida POST de alta manual sin SQL en route."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.post(
            "/tablas-comunes/bancos/nuevo/",
            data={
                "codigo": "99999",
                "nombre": "Banco manual pantalla",
                "activo": "1",
                "orden": "999",
            },
            follow_redirects=True,
        )
        banco = get_db().execute(
            "SELECT codigo, nombre FROM bancos WHERE codigo = ?",
            ("99999",),
        ).fetchone()

    assert response.status_code == 200
    assert banco["codigo"] == "99999"
    assert banco["nombre"] == "BANCO MANUAL PANTALLA"
    assert b"BANCO MANUAL PANTALLA" in response.data


def test_editar_banco_desde_pantalla():
    """Valida GET y POST de edicion manual de banco."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        get_response = client.get("/tablas-comunes/bancos/285/editar/")
        post_response = client.post(
            "/tablas-comunes/bancos/285/editar/",
            data={
                "nombre": "Banco macro pantalla",
                "activo": "1",
                "orden": "333",
            },
            follow_redirects=True,
        )
        banco = get_db().execute(
            "SELECT codigo, nombre, orden FROM bancos WHERE codigo = ?",
            ("285",),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar banco 285" in get_response.data
    assert post_response.status_code == 200
    assert banco["nombre"] == "BANCO MACRO PANTALLA"
    assert banco["orden"] == 333


def test_activar_desactivar_banco_desde_pantalla():
    """Valida POST de baja logica y reactivacion desde listado."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        desactivar_response = client.post(
            "/tablas-comunes/bancos/285/desactivar/",
            follow_redirects=True,
        )
        banco_desactivado = get_db().execute(
            "SELECT activo FROM bancos WHERE codigo = ?",
            ("285",),
        ).fetchone()
        activar_response = client.post(
            "/tablas-comunes/bancos/285/activar/",
            follow_redirects=True,
        )
        banco_activado = get_db().execute(
            "SELECT activo FROM bancos WHERE codigo = ?",
            ("285",),
        ).fetchone()

    assert desactivar_response.status_code == 200
    assert activar_response.status_code == 200
    assert banco_desactivado["activo"] == 0
    assert banco_activado["activo"] == 1
