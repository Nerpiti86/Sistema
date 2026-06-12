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
        get_db().execute(
            """
            INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("AAA00", "Banco prueba", 1, 10, "2026-01-01 10:00:00"),
        )
        response = client.get("/tablas-comunes/bancos/")

    assert response.status_code == 200
    assert b"Bancos" in response.data
    assert b"AAA00" in response.data
    assert b"Banco prueba" in response.data
    assert b'id="ba-listado"' in response.data
    assert b'id="ba-tabla"' in response.data
    assert b'data-table="bancos"' in response.data
    assert b'data-query="listar_bancos"' in response.data


def test_pantalla_tablas_comunes_bancos_muestra_sin_datos():
    """Valida mensaje vacio cuando aun no hay bancos cargados."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/bancos/")

    assert response.status_code == 200
    assert b"No hay bancos cargados." in response.data
    assert b'id="ba-row-sin-datos"' in response.data


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
