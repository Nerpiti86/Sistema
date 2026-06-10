from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_base_carga_asset_global_numero_argentino():
    """
    Contrato: la conversion de punto a coma decimal vive en asset global.

    Los templates solo declaran data-decimal="argentino" y no usan JS inline.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/indices-inflacion/")

    assert response.status_code == 200
    assert b"js/numero_argentino.js" in response.data
    assert b"<script>" not in response.data


def test_input_indice_inflacion_declara_decimal_argentino():
    """
    Contrato: los inputs decimales argentinos declaran hook estable.

    El input sigue siendo el campo real enviado por POST.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/indices-inflacion/")

    assert response.status_code == 200
    assert b'id="ec-indice-valor"' in response.data
    assert b'name="indice"' in response.data
    assert b'data-decimal="argentino"' in response.data
    assert b'inputmode="decimal"' in response.data


def test_js_numero_argentino_convierte_punto_a_coma_sin_dom_inseguro():
    """
    Contrato: el punto decimal se transforma en coma desde JS global.

    Cubre punto normal, NumpadDecimal, beforeinput y pegado de texto.
    """
    contenido = Path("app/static/js/numero_argentino.js").read_text(
        encoding="utf-8"
    )

    assert 'input[data-decimal="argentino"]' in contenido
    assert "NumpadDecimal" in contenido
    assert 'evento.key === "."' in contenido
    assert 'evento.data === "."' in contenido
    assert 'input.setRangeText(",",' in contenido
    assert 'replaceAll(".", ",")' in contenido
    assert "normalizarPegadoDecimalArgentino" in contenido
    assert "innerHTML" not in contenido
    assert ".style" not in contenido
    assert 'setAttribute("style"' not in contenido
