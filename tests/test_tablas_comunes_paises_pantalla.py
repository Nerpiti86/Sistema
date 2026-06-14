from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_pantalla_tablas_comunes_paises_responde_ok():
    """
    Valida pantalla de paises bajo Tablas Comunes.

    La route usa service shared y el template mantiene IDs cortos y data-* para
    trazabilidad tecnica de tabla, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/paises/")

    assert response.status_code == 200
    assert "Países".encode("utf-8") in response.data
    assert b'id="pa-listado"' in response.data
    assert b'id="pa-tabla"' in response.data
    assert b'data-table="paises"' in response.data
    assert b'data-query="listar_paises"' in response.data
    assert "Nuevo país".encode("utf-8") in response.data
    assert "No hay países cargados.".encode("utf-8") in response.data


def test_navbar_tiene_tablas_comunes_paises():
    """Valida acceso de navegacion Tablas Comunes > Paises."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/paises/")

    assert response.status_code == 200
    assert b"Tablas comunes" in response.data
    assert b"/tablas-comunes/paises/" in response.data
    assert b'id="ns-nav-tablas-comunes"' in response.data
    assert b'id="ns-nav-paises"' in response.data


def test_formulario_nuevo_pais_responde_ok():
    """Valida formulario de alta manual de paises."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/paises/nuevo/")

    assert response.status_code == 200
    assert "Nuevo país".encode("utf-8") in response.data
    assert b'id="pa-form"' in response.data
    assert b'id="pa-nombre"' in response.data
    assert b'id="pa-codigo-iso"' in response.data
    assert b'id="pa-orden"' in response.data
    assert b'id="pa-activo"' in response.data


def test_crear_pais_nuevo_desde_pantalla():
    """Valida POST de alta manual sin SQL en route."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.post(
            "/tablas-comunes/paises/nuevo/",
            data={
                "nombre": "Argentina",
                "codigo_iso": "ar",
                "activo": "1",
                "orden": "10",
            },
            follow_redirects=True,
        )
        pais = get_db().execute(
            "SELECT nombre, codigo_iso FROM paises WHERE codigo_iso = ?",
            ("AR",),
        ).fetchone()

    assert response.status_code == 200
    assert pais["nombre"] == "Argentina"
    assert pais["codigo_iso"] == "AR"
    assert b"Argentina" in response.data
    assert b"AR" in response.data


def test_crear_pais_nuevo_rechaza_nombre_vacio():
    """Valida respuesta 400 ante formulario invalido."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.post(
            "/tablas-comunes/paises/nuevo/",
            data={
                "nombre": "   ",
                "codigo_iso": "AR",
                "activo": "1",
                "orden": "10",
            },
        )

    assert response.status_code == 400
    assert "El nombre del pais es obligatorio.".encode("utf-8") in response.data


def test_editar_pais_desde_pantalla():
    """Valida GET y POST de edicion manual de pais."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        client.post(
            "/tablas-comunes/paises/nuevo/",
            data={
                "nombre": "Argentina",
                "codigo_iso": "AR",
                "activo": "1",
                "orden": "10",
            },
        )
        pais_creado = get_db().execute(
            "SELECT id FROM paises WHERE codigo_iso = ?",
            ("AR",),
        ).fetchone()

        get_response = client.get(f"/tablas-comunes/paises/{pais_creado['id']}/editar/")
        post_response = client.post(
            f"/tablas-comunes/paises/{pais_creado['id']}/editar/",
            data={
                "nombre": "Argentina editada",
                "codigo_iso": "ARG",
                "activo": "1",
                "orden": "15",
            },
            follow_redirects=True,
        )
        pais = get_db().execute(
            "SELECT nombre, codigo_iso, orden FROM paises WHERE id = ?",
            (pais_creado["id"],),
        ).fetchone()

    assert get_response.status_code == 200
    assert "Editar país Argentina".encode("utf-8") in get_response.data
    assert post_response.status_code == 200
    assert pais["nombre"] == "Argentina editada"
    assert pais["codigo_iso"] == "ARG"
    assert pais["orden"] == 15


def test_activar_desactivar_pais_desde_pantalla():
    """Valida POST de baja logica y reactivacion desde listado."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        client.post(
            "/tablas-comunes/paises/nuevo/",
            data={
                "nombre": "Argentina",
                "codigo_iso": "AR",
                "activo": "1",
                "orden": "10",
            },
        )
        pais_creado = get_db().execute(
            "SELECT id FROM paises WHERE codigo_iso = ?",
            ("AR",),
        ).fetchone()

        desactivar_response = client.post(
            f"/tablas-comunes/paises/{pais_creado['id']}/desactivar/",
            follow_redirects=True,
        )
        pais_desactivado = get_db().execute(
            "SELECT activo FROM paises WHERE id = ?",
            (pais_creado["id"],),
        ).fetchone()
        activar_response = client.post(
            f"/tablas-comunes/paises/{pais_creado['id']}/activar/",
            follow_redirects=True,
        )
        pais_activado = get_db().execute(
            "SELECT activo FROM paises WHERE id = ?",
            (pais_creado["id"],),
        ).fetchone()

    assert desactivar_response.status_code == 200
    assert activar_response.status_code == 200
    assert pais_desactivado["activo"] == 0
    assert pais_activado["activo"] == 1
