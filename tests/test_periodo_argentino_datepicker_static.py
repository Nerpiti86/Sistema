from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_pantalla_indices_engancha_datepicker_mensual_por_data_hook():
    """
    Contrato: el periodo de indices usa datepicker mensual transversal.

    El input nativo conserva name, value, pattern y required para no romper POST.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/indices-inflacion/")

    assert response.status_code == 200
    assert b'id="ec-indice-periodo"' in response.data
    assert b'name="periodo"' in response.data
    assert b'data-datepicker="periodo-argentino"' in response.data
    assert b'placeholder="MM/AAAA"' in response.data
    assert b'pattern="\\d{2}/\\d{4}"' in response.data
    assert b'required' in response.data
    assert b'type="month"' not in response.data


def test_js_datepicker_mensual_construye_dom_seguro_y_formato_periodo():
    """
    Contrato: el datepicker mensual usa DOM seguro y formato MM/AAAA.

    No usa innerHTML ni estilos inline; solo mejora visualmente el input real.
    """
    contenido = Path("app/static/js/fecha_argentina_datepicker.js").read_text(
        encoding="utf-8"
    )

    assert '[data-datepicker="fecha-argentina"]' in contenido
    assert '[data-datepicker="periodo-argentino"]' in contenido
    assert "document.createElement" in contenido
    assert "innerHTML" not in contenido
    assert "formatearPeriodoArgentino" in contenido
    assert "normalizarEntradaPeriodoArgentino" in contenido
    assert "datepickerPeriodo" in contenido
    assert "inicializarInputPeriodoArgentino" in contenido
    assert "String.fromCharCode(8249)" in contenido
    assert "String.fromCharCode(8250)" in contenido
    assert "\\u2039" not in contenido
    assert "\\u203a" not in contenido
    assert "ns-date-picker--periodo" in contenido
    assert ".style" not in contenido
    assert 'setAttribute("style"' not in contenido


def test_css_datepicker_mensual_define_clases_globales():
    """
    Contrato: la vista mensual vive en CSS global del datepicker.

    El template solo declara hooks data-* y no define estilos propios.
    """
    contenido = Path("app/static/css/fecha_argentina_datepicker.css").read_text(
        encoding="utf-8"
    )

    assert ".ns-date-picker--periodo" in contenido
    assert ".ns-date-picker__month-grid" in contenido
    assert ".ns-date-picker__month" in contenido
    assert ".ns-date-picker__month--selected" in contenido
    assert ".ns-date-picker__month--current" in contenido
    assert "white-space: nowrap" in contenido
