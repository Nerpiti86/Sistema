from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_base_carga_assets_globales_del_datepicker_fecha_argentina():
    """
    Contrato: el datepicker propio se carga como asset global, sin JS inline.

    Esto permite reutilizarlo en cualquier pantalla con data-datepicker sin
    repetir scripts dentro de templates.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/nuevo/")

    assert response.status_code == 200
    assert b"css/fecha_argentina_datepicker.css" in response.data
    assert b"js/fecha_argentina_datepicker.js" in response.data
    assert b"<script>" not in response.data


def test_formulario_ejercicios_contables_engancha_datepicker_por_data_hook():
    """
    Contrato: los inputs de fecha usan hook estable data-datepicker.

    El template no contiene logica de calendario; solo declara el hook visual.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/nuevo/")

    assert response.status_code == 200
    assert b'id="ec-fecha-desde"' in response.data
    assert b'id="ec-fecha-hasta"' in response.data
    assert response.data.count(b'data-datepicker="fecha-argentina"') == 2
    assert b'placeholder="DD/MM/AAAA"' in response.data
    assert b'type="date"' not in response.data


def test_js_datepicker_propio_construye_dom_seguro_y_formato_argentino():
    """
    Contrato: el datepicker construye DOM seguro y escribe fechas DD/MM/AAAA.

    No valida reglas de negocio; esa validacion sigue quedando en service.
    """
    contenido = Path("app/static/js/fecha_argentina_datepicker.js").read_text(
        encoding="utf-8"
    )

    assert '[data-datepicker="fecha-argentina"]' in contenido
    assert "document.createElement" in contenido
    assert "innerHTML" not in contenido
    assert "formatearFechaArgentina" in contenido
    assert "normalizarEntradaFechaArgentina" in contenido
    assert "datepickerDate" in contenido
    assert "datepickerAction" in contenido


def test_css_datepicker_propio_define_clases_transversales_sin_estilos_inline():
    """
    Contrato: la ubicacion y presentacion del calendario viven en CSS.

    El JS solo alterna clases/atributos y no inyecta estilos inline.
    """
    contenido = Path("app/static/css/fecha_argentina_datepicker.css").read_text(
        encoding="utf-8"
    )

    assert ".ns-date-picker" in contenido
    assert ".ns-date-picker__grid" in contenido
    assert ".ns-date-picker__day--selected" in contenido
    assert ".ns-date-picker__day--today" in contenido
    assert "position: absolute" in contenido


def test_js_datepicker_no_inyecta_estilos_inline():
    """
    Contrato: el JS no modifica style inline; la apariencia queda en CSS propio.
    """
    contenido = Path("app/static/js/fecha_argentina_datepicker.js").read_text(
        encoding="utf-8"
    )

    assert ".style" not in contenido
    assert "setAttribute(\"style\"" not in contenido
