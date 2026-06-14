from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_pantalla_condiciones_iva_responde_ok():
    """Valida listado de condiciones frente al IVA en Tablas comunes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/condiciones-iva/")

    assert response.status_code == 200
    assert b"Condiciones frente al IVA" in response.data
    assert b"Consumidor Final" in response.data
    assert b'id="civa-listado"' in response.data
    assert b'id="civa-tabla"' in response.data


def test_pantalla_tipos_documento_responde_ok():
    """Valida listado de tipos de documento en Tablas comunes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/tipos-documento/")

    assert response.status_code == 200
    assert b"Tipos de documento" in response.data
    assert b"CUIT" in response.data
    assert b"DNI" in response.data
    assert b'id="tdoc-listado"' in response.data
    assert b'id="tdoc-tabla"' in response.data


def test_editar_condicion_iva_desde_pantalla():
    """Valida GET y POST de edicion de condicion frente al IVA."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        get_response = client.get("/tablas-comunes/condiciones-iva/5/editar/")
        post_response = client.post(
            "/tablas-comunes/condiciones-iva/5/editar/",
            data={
                "descripcion": "Consumidor Final pantalla",
                "activo": "1",
                "orden": "31",
            },
            follow_redirects=True,
        )
        condicion = get_db().execute(
            "SELECT codigo, descripcion, orden FROM condiciones_iva WHERE codigo = ?",
            ("5",),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar condici" in get_response.data
    assert b"5 - Consumidor Final" in get_response.data
    assert post_response.status_code == 200
    assert condicion["descripcion"] == "Consumidor Final pantalla"
    assert condicion["orden"] == 31


def test_editar_tipo_documento_desde_pantalla():
    """Valida GET y POST de edicion de tipo de documento."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        get_response = client.get("/tablas-comunes/tipos-documento/80/editar/")
        post_response = client.post(
            "/tablas-comunes/tipos-documento/80/editar/",
            data={
                "descripcion": "CUIT pantalla",
                "activo": "1",
                "orden": "11",
            },
            follow_redirects=True,
        )
        tipo = get_db().execute(
            "SELECT codigo, descripcion, orden FROM tipos_documento WHERE codigo = ?",
            ("80",),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar tipo de documento 80 - CUIT" in get_response.data
    assert post_response.status_code == 200
    assert tipo["descripcion"] == "CUIT pantalla"
    assert tipo["orden"] == 11


def test_navbar_tiene_catalogos_fiscales():
    """Valida accesos de navegacion para catalogos fiscales comunes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/condiciones-iva/")

    assert response.status_code == 200
    assert b'id="ns-nav-tablas-comunes"' in response.data
    assert b'id="ns-nav-condiciones-iva"' in response.data
    assert b'id="ns-nav-tipos-documento"' in response.data
    assert b"/tablas-comunes/condiciones-iva/" in response.data
    assert b"/tablas-comunes/tipos-documento/" in response.data


def test_routes_catalogos_fiscales_no_usan_sql_directo():
    """Valida que routes fiscales no usen SQL ni get_db."""
    contenido = Path("app/tablas_comunes/routes_catalogos_fiscales.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_service_catalogos_fiscales_no_usa_sql_directo():
    """Valida que service fiscal delega persistencia al repository."""
    contenido = Path("app/shared/catalogos_fiscales_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido
