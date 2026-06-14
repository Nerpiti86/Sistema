from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.grupos_clientes_repository import crear_grupo_cliente


def test_gestion_register_existe_y_modules_registra_gestion():
    """Valida registro del modulo gestion dentro del factory principal."""
    init_contenido = Path("app/gestion/__init__.py").read_text(encoding="utf-8")
    modules_contenido = Path("app/modules.py").read_text(encoding="utf-8")

    assert "def register(app):" in init_contenido
    assert "app.register_blueprint(bp)" in init_contenido
    assert "register_gestion" in modules_contenido
    assert "register_gestion(app)" in modules_contenido


def test_routes_gestion_no_usan_sql_directo():
    """Valida que routes de gestion deleguen persistencia al service."""
    contenido = Path("app/gestion/routes.py").read_text(encoding="utf-8")

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_pantalla_gestion_grupos_clientes_responde_ok_sin_datos():
    """
    Valida pantalla de grupos de clientes bajo Gestion.

    La route usa service y el template mantiene IDs cortos y data-* para
    trazabilidad tecnica de tabla, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/clientes/grupos/")

    assert response.status_code == 200
    assert b"Grupos de clientes" in response.data
    assert b"No hay grupos de clientes cargados." in response.data
    assert b'id="gc-listado"' in response.data
    assert b'id="gc-tabla"' in response.data
    assert b'data-table="grupos_clientes"' in response.data
    assert b'data-query="listar_grupos_clientes"' in response.data
    assert b"Nuevo grupo" in response.data


def test_pantalla_gestion_grupos_clientes_muestra_datos():
    """Valida que el listado muestre grupos cargados por repository."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})
        crear_grupo_cliente({"nombre": "Mayorista", "activo": 1, "orden": 20})
        response = client.get("/gestion/clientes/grupos/")

    assert response.status_code == 200
    assert b"Particular" in response.data
    assert b"Mayorista" in response.data
    assert b"Editar" in response.data
    assert b"Desactivar" in response.data


def test_navbar_tiene_gestion_grupos_clientes():
    """Valida acceso de navegacion Gestion > Clientes > Grupos de clientes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/clientes/grupos/")

    assert response.status_code == 200
    assert b"Gesti" in response.data
    assert b"/gestion/clientes/grupos/" in response.data
    assert b'id="ns-nav-gestion"' in response.data
    assert b'id="ns-nav-grupos-clientes"' in response.data


def test_formulario_nuevo_grupo_cliente_responde_ok():
    """Valida formulario de alta manual de grupos de clientes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/gestion/clientes/grupos/nuevo/")

    assert response.status_code == 200
    assert b"Nuevo grupo de clientes" in response.data
    assert b'id="gc-form"' in response.data
    assert b'id="gc-nombre"' in response.data
    assert b'id="gc-orden"' in response.data
    assert b'id="gc-activo"' in response.data


def test_crear_grupo_cliente_nuevo_desde_pantalla():
    """Valida POST de alta manual sin SQL en route."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.post(
            "/gestion/clientes/grupos/nuevo/",
            data={
                "nombre": "Particular",
                "activo": "1",
                "orden": "10",
            },
            follow_redirects=True,
        )
        grupo = get_db().execute(
            "SELECT nombre, activo, orden FROM grupos_clientes WHERE nombre = ?",
            ("Particular",),
        ).fetchone()

    assert response.status_code == 200
    assert grupo["nombre"] == "Particular"
    assert grupo["activo"] == 1
    assert grupo["orden"] == 10
    assert b"Particular" in response.data


def test_crear_grupo_cliente_nuevo_rechaza_nombre_vacio():
    """Valida respuesta 400 cuando el service rechaza el formulario."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.post(
            "/gestion/clientes/grupos/nuevo/",
            data={
                "nombre": "   ",
                "activo": "1",
                "orden": "10",
            },
        )

    assert response.status_code == 400
    assert b"El nombre del grupo de clientes es obligatorio." in response.data


def test_editar_grupo_cliente_desde_pantalla():
    """Valida GET y POST de edicion manual de grupo de clientes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        get_response = client.get(f"/gestion/clientes/grupos/{grupo['id']}/editar/")
        post_response = client.post(
            f"/gestion/clientes/grupos/{grupo['id']}/editar/",
            data={
                "nombre": "Particular editado",
                "activo": "1",
                "orden": "15",
            },
            follow_redirects=True,
        )
        grupo_actualizado = get_db().execute(
            "SELECT nombre, orden FROM grupos_clientes WHERE id = ?",
            (grupo["id"],),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar grupo de clientes Particular" in get_response.data
    assert post_response.status_code == 200
    assert grupo_actualizado["nombre"] == "Particular editado"
    assert grupo_actualizado["orden"] == 15


def test_activar_desactivar_grupo_cliente_desde_pantalla():
    """Valida POST de baja logica y reactivacion desde listado."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        desactivar_response = client.post(
            f"/gestion/clientes/grupos/{grupo['id']}/desactivar/",
            follow_redirects=True,
        )
        grupo_desactivado = get_db().execute(
            "SELECT activo FROM grupos_clientes WHERE id = ?",
            (grupo["id"],),
        ).fetchone()
        activar_response = client.post(
            f"/gestion/clientes/grupos/{grupo['id']}/activar/",
            follow_redirects=True,
        )
        grupo_activado = get_db().execute(
            "SELECT activo FROM grupos_clientes WHERE id = ?",
            (grupo["id"],),
        ).fetchone()

    assert desactivar_response.status_code == 200
    assert activar_response.status_code == 200
    assert grupo_desactivado["activo"] == 0
    assert grupo_activado["activo"] == 1
