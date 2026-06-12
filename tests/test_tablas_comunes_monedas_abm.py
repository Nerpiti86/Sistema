from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_formulario_nueva_moneda_responde_ok():
    """Valida formulario de alta manual de monedas."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/monedas/nueva/")

    assert response.status_code == 200
    assert b"Nueva moneda" in response.data
    assert b'id="mo-form"' in response.data
    assert b'id="mo-codigo"' in response.data
    assert b'id="mo-nombre"' in response.data


def test_crear_moneda_nueva_desde_pantalla():
    """Valida POST de alta manual de moneda."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.post(
            "/tablas-comunes/monedas/nueva/",
            data={
                "codigo": "uyu",
                "nombre": "Peso uruguayo pantalla",
                "simbolo": "$U",
                "decimales": "2",
                "activa": "1",
                "orden": "40",
            },
            follow_redirects=True,
        )
        moneda = get_db().execute(
            "SELECT codigo, nombre FROM monedas WHERE codigo = ?",
            ("UYU",),
        ).fetchone()

    assert response.status_code == 200
    assert moneda["codigo"] == "UYU"
    assert moneda["nombre"] == "Peso uruguayo pantalla"
    assert b"Peso uruguayo pantalla" in response.data


def test_editar_moneda_desde_pantalla():
    """Valida GET y POST de edicion manual de moneda."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        get_response = client.get("/tablas-comunes/monedas/USD/editar/")
        post_response = client.post(
            "/tablas-comunes/monedas/USD/editar/",
            data={
                "nombre": "Dolar pantalla",
                "simbolo": "USD",
                "decimales": "2",
                "activa": "1",
                "orden": "25",
            },
            follow_redirects=True,
        )
        moneda = get_db().execute(
            "SELECT codigo, nombre, orden FROM monedas WHERE codigo = ?",
            ("USD",),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar moneda USD" in get_response.data
    assert post_response.status_code == 200
    assert moneda["nombre"] == "Dolar pantalla"
    assert moneda["orden"] == 25


def test_activar_desactivar_moneda_desde_pantalla():
    """Valida POST de baja logica y reactivacion."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        desactivar_response = client.post(
            "/tablas-comunes/monedas/USD/desactivar/",
            follow_redirects=True,
        )
        moneda_desactivada = get_db().execute(
            "SELECT activa FROM monedas WHERE codigo = ?",
            ("USD",),
        ).fetchone()
        activar_response = client.post(
            "/tablas-comunes/monedas/USD/activar/",
            follow_redirects=True,
        )
        moneda_activada = get_db().execute(
            "SELECT activa FROM monedas WHERE codigo = ?",
            ("USD",),
        ).fetchone()

    assert desactivar_response.status_code == 200
    assert activar_response.status_code == 200
    assert moneda_desactivada["activa"] == 0
    assert moneda_activada["activa"] == 1
