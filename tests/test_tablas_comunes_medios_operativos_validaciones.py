from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_formulario_medios_operativos_expone_validaciones_visuales():
    """
    Valida hooks HTML y asset JS externo para campos visuales condicionales.

    El contrato actual evita JS inline: el template declara data-* y el
    comportamiento vive en app/static/js/medios_operativos_form.js.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/medios-operativos/nuevo/")

    assert response.status_code == 200
    assert b'data-mope-bank-field' in response.data
    assert b'data-mope-currency-field' in response.data
    assert b'js/medios_operativos_form.js' in response.data

    contenido_js = Path("app/static/js/medios_operativos_form.js").read_text(
        encoding="utf-8"
    )

    assert 'const TIPO_BANCO_PROPIO = "BANCO_PROPIO"' in contenido_js
    assert 'const MONEDA_CONTABLE = "ARS"' in contenido_js
    assert "actualizarCamposBanco" in contenido_js
    assert "actualizarCamposCotizacion" in contenido_js


def test_formulario_medios_operativos_valida_cuenta_contable_visual():
    """
    Valida lookup visual de cuenta contable imputable en medios operativos.

    El endpoint se genera con url_for en el template y el JS externo lo lee
    desde data-cuentas-imputables-url.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/medios-operativos/nuevo/")

    assert response.status_code == 200
    assert b'id="mope-cuenta-contable"' in response.data
    assert b'id="mope-cuenta-contable-estado"' in response.data
    assert b'id="mope-cuentas-contables-lista"' in response.data
    assert b'data-cuentas-imputables-url=' in response.data
    assert b'/contabilidad/cuentas-contables/imputables/buscar/' in response.data

    contenido_js = Path("app/static/js/medios_operativos_form.js").read_text(
        encoding="utf-8"
    )

    assert "validarCuentaContableVisual" in contenido_js
    assert "dataset.cuentasImputablesUrl" in contenido_js
    assert "dataset.cuentasImputablesLimite" in contenido_js
    assert "fetch(" in contenido_js
    assert "/contabilidad/cuentas-contables/imputables/buscar/" not in contenido_js
