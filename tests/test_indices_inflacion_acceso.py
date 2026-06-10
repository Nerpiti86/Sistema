from app import create_app
from app.config import TestConfig


def test_index_contabilidad_muestra_acceso_a_indices_inflacion():
    """
    Valida acceso visible a la carga de indices de inflacion.

    El acceso usa ID y data-action estables para no depender solo del texto.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b'id="ec-indices-acceso"' in response.data
    assert b'data-table="indices_inflacion"' in response.data
    assert b'data-action="ver_indices_inflacion"' in response.data
    assert b"/contabilidad/indices-inflacion/" in response.data
    assert "Índices de inflación".encode("utf-8") in response.data
