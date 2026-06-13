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
