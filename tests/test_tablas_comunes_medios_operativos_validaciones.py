from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_formulario_medios_operativos_expone_validaciones_visuales():
    """Valida JS/atributos para deshabilitar campos no aplicables en pantalla."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/medios-operativos/nuevo/")

    assert response.status_code == 200
    assert b'data-mope-bank-field' in response.data
    assert b'data-mope-currency-field' in response.data
    assert b'const usaBanco = tipo && tipo.value === "BANCO_PROPIO"' in response.data
    assert b'const monedaEsArs = moneda && moneda.value === "ARS"' in response.data
    assert b'actualizarCamposBanco' in response.data
    assert b'actualizarCamposCotizacion' in response.data


def test_formulario_medios_operativos_valida_cuenta_contable_visual():
    """Valida lookup visual de cuenta contable imputable en medios operativos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/medios-operativos/nuevo/")

    assert response.status_code == 200
    assert b'id="mope-cuenta-contable"' in response.data
    assert b'id="mope-cuenta-contable-estado"' in response.data
    assert b'id="mope-cuentas-contables-lista"' in response.data
    assert b'/contabilidad/cuentas-contables/imputables/buscar/' in response.data
    assert b'validarCuentaContableVisual' in response.data
    assert b'setCustomValidity' in response.data
    assert b'La cuenta contable no existe o no es imputable.' in response.data
