from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.paises_repository import crear_pais
from app.shared.provincias_repository import crear_provincia


def _crear_pais(nombre="Argentina", codigo_iso="AR", activo=1, orden=10):
    return crear_pais(
        {
            "nombre": nombre,
            "codigo_iso": codigo_iso,
            "activo": activo,
            "orden": orden,
        }
    )


def test_pantalla_tablas_comunes_provincias_responde_ok():
    """
    Valida pantalla de provincias bajo Tablas Comunes.

    La route usa service shared y el template mantiene IDs cortos y data-* para
    trazabilidad tecnica de tabla, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/provincias/")

    assert response.status_code == 200
    assert b"Provincias" in response.data
    assert b'id="pv-listado"' in response.data
    assert b'id="pv-tabla"' in response.data
    assert b'data-table="provincias"' in response.data
    assert b'data-query="listar_provincias"' in response.data
    assert b"Nueva provincia" in response.data
    assert b"No hay provincias cargadas." in response.data


def test_pantalla_tablas_comunes_provincias_muestra_pais_y_provincia():
    """Valida render de pais y provincia cargados."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        crear_provincia(
            {
                "pais_id": argentina["id"],
                "nombre": "Santa Fe",
                "activo": 1,
                "orden": 10,
            }
        )

        response = client.get("/tablas-comunes/provincias/")

    assert response.status_code == 200
    assert b"Argentina (AR)" in response.data
    assert b"Santa Fe" in response.data
    assert b"Editar" in response.data
    assert b"Desactivar" in response.data


def test_navbar_tiene_tablas_comunes_provincias():
    """Valida acceso de navegacion Tablas Comunes > Provincias."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/provincias/")

    assert response.status_code == 200
    assert b"Tablas comunes" in response.data
    assert b"/tablas-comunes/provincias/" in response.data
    assert b'id="ns-nav-tablas-comunes"' in response.data
    assert b'id="ns-nav-provincias"' in response.data


def test_formulario_nueva_provincia_responde_ok():
    """Valida formulario de alta manual de provincias."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_pais()
        response = client.get("/tablas-comunes/provincias/nuevo/")

    assert response.status_code == 200
    assert b"Nueva provincia" in response.data
    assert b'id="pv-form"' in response.data
    assert b'id="pv-pais"' in response.data
    assert b'id="pv-nombre"' in response.data
    assert b'id="pv-orden"' in response.data
    assert b'id="pv-activo"' in response.data
    assert b"Argentina (AR)" in response.data


def test_formulario_nueva_provincia_sin_paises_activos_responde_ok():
    """Valida que el formulario avise cuando no hay paises activos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/provincias/nuevo/")

    assert response.status_code == 200
    assert b'id="pv-alerta-sin-paises"' in response.data
    assert b"primero debe existir al menos un pa" in response.data


def test_crear_provincia_nueva_desde_pantalla():
    """Valida POST de alta manual sin SQL en route."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        response = client.post(
            "/tablas-comunes/provincias/nuevo/",
            data={
                "pais_id": str(argentina["id"]),
                "nombre": "Santa Fe",
                "activo": "1",
                "orden": "10",
            },
            follow_redirects=True,
        )
        provincia = get_db().execute(
            "SELECT pais_id, nombre FROM provincias WHERE nombre = ?",
            ("Santa Fe",),
        ).fetchone()

    assert response.status_code == 200
    assert provincia["pais_id"] == argentina["id"]
    assert provincia["nombre"] == "Santa Fe"
    assert b"Santa Fe" in response.data
    assert b"Argentina (AR)" in response.data


def test_crear_provincia_nueva_rechaza_pais_inactivo():
    """Valida respuesta 400 al intentar crear contra pais inactivo."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        pais = _crear_pais("Pais inactivo", "PI", activo=0)
        response = client.post(
            "/tablas-comunes/provincias/nuevo/",
            data={
                "pais_id": str(pais["id"]),
                "nombre": "Provincia",
                "activo": "1",
                "orden": "10",
            },
        )

    assert response.status_code == 400
    assert b"El pais no existe o no esta activo." in response.data


def test_editar_provincia_desde_pantalla():
    """Valida GET y POST de edicion manual de provincia."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia_creada = crear_provincia(
            {
                "pais_id": argentina["id"],
                "nombre": "Santa Fe",
                "activo": 1,
                "orden": 10,
            }
        )

        get_response = client.get(
            f"/tablas-comunes/provincias/{provincia_creada['id']}/editar/"
        )
        post_response = client.post(
            f"/tablas-comunes/provincias/{provincia_creada['id']}/editar/",
            data={
                "pais_id": str(argentina["id"]),
                "nombre": "Santa Fe editada",
                "activo": "1",
                "orden": "15",
            },
            follow_redirects=True,
        )
        provincia = get_db().execute(
            "SELECT pais_id, nombre, orden FROM provincias WHERE id = ?",
            (provincia_creada["id"],),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar provincia Santa Fe" in get_response.data
    assert post_response.status_code == 200
    assert provincia["pais_id"] == argentina["id"]
    assert provincia["nombre"] == "Santa Fe editada"
    assert provincia["orden"] == 15


def test_activar_desactivar_provincia_desde_pantalla():
    """Valida POST de baja logica y reactivacion desde listado."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia_creada = crear_provincia(
            {
                "pais_id": argentina["id"],
                "nombre": "Santa Fe",
                "activo": 1,
                "orden": 10,
            }
        )

        desactivar_response = client.post(
            f"/tablas-comunes/provincias/{provincia_creada['id']}/desactivar/",
            follow_redirects=True,
        )
        provincia_desactivada = get_db().execute(
            "SELECT activo FROM provincias WHERE id = ?",
            (provincia_creada["id"],),
        ).fetchone()
        activar_response = client.post(
            f"/tablas-comunes/provincias/{provincia_creada['id']}/activar/",
            follow_redirects=True,
        )
        provincia_activada = get_db().execute(
            "SELECT activo FROM provincias WHERE id = ?",
            (provincia_creada["id"],),
        ).fetchone()

    assert desactivar_response.status_code == 200
    assert activar_response.status_code == 200
    assert provincia_desactivada["activo"] == 0
    assert provincia_activada["activo"] == 1
