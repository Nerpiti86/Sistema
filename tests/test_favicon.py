from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_favicon_svg_existe_y_es_svg():
    """Contrato: el favicon versionado vive en static/img como SVG."""
    contenido = Path("app/static/img/favicon.svg").read_text(encoding="utf-8")

    assert "<svg" in contenido.lower()
    assert len(contenido.strip()) > 0


def test_base_declara_favicon_svg_y_shortcut_icon():
    """
    Contrato: el layout informa el favicon al navegador.

    El icono principal apunta al SVG estatico y el shortcut apunta a /favicon.ico.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/nuevo/")

    assert response.status_code == 200
    assert b'rel="icon"' in response.data
    assert b'type="image/svg+xml"' in response.data
    assert b"img/favicon.svg" in response.data
    assert b'rel="shortcut icon"' in response.data
    assert b"/favicon.ico" in response.data


def test_favicon_ico_no_devuelve_404():
    """Contrato: /favicon.ico responde para no ensuciar la consola del servidor."""
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"
