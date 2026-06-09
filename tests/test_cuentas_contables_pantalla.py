from app import create_app
from app.config import TestConfig


def test_pantalla_cuentas_contables_responde_ok():
    """
    Valida la pantalla base de cuentas_contables.

    Este paso solo registra acceso visual y route inicial. No crea tabla,
    repository ni service para no mezclarlo con el modelo de datos.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/cuentas-contables/")

    assert response.status_code == 200
    assert b"Cuentas contables" in response.data
    assert b'id="cc-listado"' in response.data
    assert b'data-table="cuentas_contables"' in response.data
    assert b'data-query="listar_cuentas_contables"' in response.data
    assert b'id="cc-mensaje-pendiente"' in response.data


def test_pantalla_contabilidad_tiene_acceso_a_cuentas_contables():
    """
    Valida acceso desde Contabilidad hacia Cuentas contables.

    El modulo se nombra como Cuentas contables. El contrato jerarquico
    queda para un paso posterior y separado.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Cuentas contables" in response.data
    assert b"/contabilidad/cuentas-contables/" in response.data
    assert b'id="cc-acceso"' in response.data
    assert b'data-table="cuentas_contables"' in response.data
