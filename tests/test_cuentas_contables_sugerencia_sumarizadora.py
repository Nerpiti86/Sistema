from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_formulario_cuentas_contables_expone_sumarizadora_derivada_readonly():
    """
    Valida contrato visual de sumarizadora derivada.

    El usuario carga Cuenta. El formulario calcula Sumarizadora en un input
    readonly y luego el lookup completa Descripcion sumarizadora.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/cuentas-contables/nueva/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="cc-cuenta"' in html
    assert 'id="cc-sumarizadora"' in html
    assert 'data-derived="cuentas-contables-sumarizadora-desde-cuenta"' in html
    assert 'data-lookup="cuentas-contables-descripcion-sumarizadora"' in html
    assert 'readonly' in html
    assert "js/cuentas_contables_form_lookup_sumarizadora.js" in html
    assert "js/cuentas_contables_form_sugerencia_sumarizadora.js" in html


def test_js_sugerencia_sumarizadora_tiene_nombres_identificables():
    """
    Valida nombres explicitos del JS de sumarizadora derivada.

    No se aceptan funciones genericas: cada nombre debe indicar que calcula o
    aplica la sumarizadora desde la cuenta contable.
    """
    with open(
        "app/static/js/cuentas_contables_form_sugerencia_sumarizadora.js",
        encoding="utf-8",
    ) as archivo_js:
        contenido = archivo_js.read()

    assert "CUENTAS_CONTABLES_SELECTOR_CUENTA_PARA_SUMARIZADORA" in contenido
    assert "CUENTAS_CONTABLES_SELECTOR_SUMARIZADORA_DERIVADA" in contenido
    assert "CUENTAS_CONTABLES_REGEX_CUENTA_PARA_SUMARIZADORA" in contenido
    assert "calcularSumarizadoraDerivadaDesdeCuentaContable" in contenido
    assert "aplicarSumarizadoraDerivadaDesdeCuentaContable" in contenido
    assert "dispararLookupDescripcionSumarizadoraCuentaContable" in contenido
    assert "inicializarSugerenciaSumarizadoraDesdeCuentaContable" in contenido


def test_js_sugerencia_sumarizadora_contiene_reglas_de_derivacion():
    """
    Valida reglas documentadas en codigo JS.

    Las raices no tienen sumarizadora. Las cuentas hijas derivan al nivel padre
    inmediato reemplazando el ultimo segmento significativo por ceros.
    """
    with open(
        "app/static/js/cuentas_contables_form_sugerencia_sumarizadora.js",
        encoding="utf-8",
    ) as archivo_js:
        contenido = archivo_js.read()

    assert 'cuentaAnaliticaContable !== "000"' in contenido
    assert 'subrubroCuentaContable !== "00"' in contenido
    assert 'rubroCuentaContable !== "00"' in contenido
    assert 'grupoCuentaContable !== "0"' in contenido
    assert 'return "";' in contenido
