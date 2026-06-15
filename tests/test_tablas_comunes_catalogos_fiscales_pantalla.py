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


def test_pantalla_unidades_medida_responde_ok():
    """Valida listado de unidades de medida en Tablas comunes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/unidades-medida/")

    assert response.status_code == 200
    assert b"Unidades de medida" in response.data
    assert b"kilogramos" in response.data
    assert b"unidades" in response.data
    assert b'id="umed-listado"' in response.data
    assert b'id="umed-tabla"' in response.data


def test_pantalla_tipos_bonificacion_responde_ok():
    """Valida listado de tipos de bonificacion en Tablas comunes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/tipos-bonificacion/")

    assert response.status_code == 200
    assert b"Tipos de bonificaci" in response.data
    assert b"Porcentaje" in response.data
    assert b"Monto" in response.data
    assert b'id="tbon-listado"' in response.data
    assert b'id="tbon-tabla"' in response.data


def test_pantalla_tipos_comprobante_responde_ok():
    """Valida listado de tipos de comprobante en Tablas comunes."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/tipos-comprobante/")

    assert response.status_code == 200
    assert b"Tipos de comprobantes" in response.data
    assert b"001" in response.data
    assert b"FACTURA A" in response.data
    assert b"FACTURA DE CR" in response.data
    assert b'id="tcomp-listado"' in response.data
    assert b'id="tcomp-tabla"' in response.data


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


def test_editar_unidad_medida_desde_pantalla():
    """Valida GET y POST de edicion de unidad de medida."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        get_response = client.get("/tablas-comunes/unidades-medida/7/editar/")
        post_response = client.post(
            "/tablas-comunes/unidades-medida/7/editar/",
            data={
                "descripcion": "unidades pantalla",
                "activo": "1",
                "orden": "61",
            },
            follow_redirects=True,
        )
        unidad = get_db().execute(
            "SELECT codigo, descripcion, orden FROM unidades_medida WHERE codigo = ?",
            ("7",),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar unidad de medida 7 - unidades" in get_response.data
    assert post_response.status_code == 200
    assert unidad["descripcion"] == "unidades pantalla"
    assert unidad["orden"] == 61


def test_editar_tipo_bonificacion_desde_pantalla():
    """Valida GET y POST de edicion de tipo de bonificacion."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        get_response = client.get("/tablas-comunes/tipos-bonificacion/1/editar/")
        post_response = client.post(
            "/tablas-comunes/tipos-bonificacion/1/editar/",
            data={
                "descripcion": "Porcentaje pantalla",
                "activo": "1",
                "orden": "11",
            },
            follow_redirects=True,
        )
        tipo = get_db().execute(
            "SELECT codigo, descripcion, orden FROM tipos_bonificacion WHERE codigo = ?",
            ("1",),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar tipo de bonificaci" in get_response.data
    assert post_response.status_code == 200
    assert tipo["descripcion"] == "Porcentaje pantalla"
    assert tipo["orden"] == 11


def test_editar_tipo_comprobante_desde_pantalla():
    """Valida GET y POST de edicion de tipo de comprobante."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        get_response = client.get("/tablas-comunes/tipos-comprobante/001/editar/")
        post_response = client.post(
            "/tablas-comunes/tipos-comprobante/001/editar/",
            data={
                "descripcion": "FACTURA A pantalla",
                "activo": "1",
                "orden": "11",
            },
            follow_redirects=True,
        )
        tipo = get_db().execute(
            "SELECT codigo, descripcion, orden FROM tipos_comprobante WHERE codigo = ?",
            ("001",),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar tipo de comprobante 001 - FACTURA A" in get_response.data
    assert post_response.status_code == 200
    assert tipo["descripcion"] == "FACTURA A pantalla"
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
    assert b'id="ns-nav-unidades-medida"' in response.data
    assert b'id="ns-nav-tipos-bonificacion"' in response.data
    assert b'id="ns-nav-tipos-comprobante"' in response.data
    assert b"/tablas-comunes/condiciones-iva/" in response.data
    assert b"/tablas-comunes/tipos-documento/" in response.data
    assert b"/tablas-comunes/unidades-medida/" in response.data
    assert b"/tablas-comunes/tipos-bonificacion/" in response.data
    assert b"/tablas-comunes/tipos-comprobante/" in response.data


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
