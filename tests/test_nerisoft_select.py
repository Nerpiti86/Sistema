from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_base_carga_assets_globales_del_select_propio():
    """
    Contrato: el select propio se carga como JS/CSS global reutilizable.

    Los templates solo declaran data-ns-select y el select nativo conserva name.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/nuevo/")

    assert response.status_code == 200
    assert b"css/nerisoft_select.css" in response.data
    assert b"js/nerisoft_select.js" in response.data


def test_ejercicios_contables_usa_select_propio_normal_sin_perder_select_nativo():
    """
    Contrato: estado y fase cierre usan select visual normal.

    El select nativo queda en el HTML para mantener POST, required y valores.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/nuevo/")

    assert response.status_code == 200
    assert b'id="ec-estado"' in response.data
    assert b'id="ec-fase-cierre"' in response.data
    assert response.data.count(b'data-ns-select="normal"') == 2
    assert b'name="estado"' in response.data
    assert b'name="fase_cierre"' in response.data


def test_cuentas_contables_usa_select_propio_normal_sin_perder_select_nativo():
    """
    Contrato: saldo habitual y naturaleza usan select visual normal.

    El select nativo sigue estando disponible para validacion y submit.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/cuentas-contables/nueva/")

    assert response.status_code == 200
    assert b'id="cc-saldo-habitual"' in response.data
    assert b'id="cc-naturaleza"' in response.data
    assert response.data.count(b'data-ns-select="normal"') == 2
    assert b'name="saldo_habitual"' in response.data
    assert b'name="naturaleza"' in response.data


def test_js_select_soporta_modo_normal_y_search_sin_innerhtml():
    """
    Contrato: el JS propio soporta select normal y select con busqueda.

    No usa innerHTML; construye DOM mediante createElement.
    """
    contenido = Path("app/static/js/nerisoft_select.js").read_text(encoding="utf-8")

    assert 'select[data-ns-select]' in contenido
    assert 'modo === "search"' in contenido
    assert "ns-select__search" in contenido
    assert "document.createElement" in contenido
    assert "innerHTML" not in contenido
    assert "dispatchEvent(new Event(\"change\"" in contenido


def test_js_select_tiene_interaccion_por_teclado_y_busqueda_rapida():
    """
    Contrato: el select propio se puede usar con teclado.

    Flechas, Home/End, Enter, Escape y busqueda rapida no dependen del mouse.
    """
    contenido = Path("app/static/js/nerisoft_select.js").read_text(encoding="utf-8")

    assert "ArrowDown" in contenido
    assert "ArrowUp" in contenido
    assert "Home" in contenido
    assert "End" in contenido
    assert "buscarPorTecladoRapido" in contenido
    assert "estado.busquedaRapida ||" in contenido
    assert "pintarOpciones(estado)" in contenido
    assert "seleccionarOpcionActiva" in contenido
    assert "scrollIntoView" in contenido
    assert "aria-activedescendant" in contenido


def test_css_select_define_clases_para_normal_search_y_estado_interactivo():
    """
    Contrato: la apariencia del select vive en CSS propio.

    Tambien define estado abierto, opcion activa y microinteracciones.
    """
    contenido = Path("app/static/css/nerisoft_select.css").read_text(encoding="utf-8")

    assert ".ns-select" in contenido
    assert ".ns-select__control" in contenido
    assert ".ns-select__panel" in contenido
    assert ".ns-select__search" in contenido
    assert ".ns-select__option--selected" in contenido
    assert ".ns-select--open" in contenido
    assert ".ns-select__option--active" in contenido
    assert "transform: rotate(180deg)" in contenido
