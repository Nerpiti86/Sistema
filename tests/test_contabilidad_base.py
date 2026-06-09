from app import create_app
from app.config import TestConfig


def test_modulo_contabilidad_responde_ok():
    """Valida que el modulo contabilidad se registre y responda."""
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Contabilidad" in response.data
