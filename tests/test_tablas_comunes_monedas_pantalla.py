from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_pantalla_tablas_comunes_monedas_responde_ok():
    """
    Valida pantalla de monedas bajo Tablas Comunes.

    La route usa service y el template mantiene IDs cortos y data-* para
    trazabilidad tecnica de tabla, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/monedas/")

    assert response.status_code == 200
    assert b"Monedas" in response.data
    assert b"ARS" in response.data
    assert b"USD" in response.data
    assert b"EUR" in response.data
    assert b'id="mo-listado"' in response.data
    assert b'id="mo-tabla"' in response.data
    assert b'data-table="monedas"' in response.data
    assert b'data-query="listar_monedas"' in response.data


def test_navbar_tiene_tablas_comunes_monedas():
    """
    Valida acceso de navegacion Tablas Comunes > Monedas.

    Las cotizaciones no tienen acceso de menu porque se registran por operacion.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/monedas/")

    assert response.status_code == 200
    assert b"Tablas comunes" in response.data
    assert b"/tablas-comunes/monedas/" in response.data
    assert b'id="ns-nav-tablas-comunes"' in response.data
    assert b'id="ns-nav-monedas"' in response.data
    assert b"monedas_cotizaciones" not in response.data


def test_tablas_comunes_routes_no_exponen_cotizaciones():
    """
    Valida que Tablas Comunes solo exponga Monedas en esta etapa.

    Las cotizaciones quedan como soporte interno de operaciones, sin pantalla.
    """
    contenido = Path("app/tablas_comunes/routes.py").read_text(
        encoding="utf-8"
    )

    assert "monedas_cotizaciones" not in contenido
    assert "cotizaciones" not in contenido


def test_routes_tablas_comunes_no_usan_sql_directo():
    """Valida que las routes de Tablas Comunes no usen SQL ni get_db."""
    contenido = Path("app/tablas_comunes/routes.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido
