from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.coeficientes_inflacion_repository import (
    obtener_indice_inflacion,
)


def test_get_indices_inflacion_muestra_formulario_y_estado_vacio():
    """
    Valida pantalla inicial de carga de indices.

    El formulario mantiene names reales para POST y usa IDs estables para tests.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.get("/contabilidad/indices-inflacion/")

    assert response.status_code == 200
    assert b'id="ec-indices"' in response.data
    assert b'id="ec-indice-form"' in response.data
    assert b'id="ec-indice-periodo"' in response.data
    assert b'name="periodo"' in response.data
    assert b'data-datepicker="periodo-argentino"' in response.data
    assert b'placeholder="MM/AAAA"' in response.data
    assert b'pattern="\\d{2}/\\d{4}"' in response.data
    assert b'type="month"' not in response.data
    assert b'id="ec-indice-valor"' in response.data
    assert b'name="indice"' in response.data
    assert b'id="ec-indices-vacio"' in response.data


def test_post_indices_inflacion_guarda_y_redirige():
    """
    Valida POST de indices sin SQL en route.

    La route delega normalizacion y persistencia en service.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.post(
            "/contabilidad/indices-inflacion/",
            data={
                "periodo": "04/2025",
                "indice": "1.234,5678",
            },
            follow_redirects=False,
        )
        indice = obtener_indice_inflacion(202504)

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/indices-inflacion/?periodo=202504"
    )
    assert indice["periodo_yyyymm"] == 202504
    assert indice["indice_10000"] == 12_345_678


def test_get_indices_inflacion_muestra_listado_formateado():
    """
    Valida render del listado de indices con formatos preparados por service.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        client.post(
            "/contabilidad/indices-inflacion/",
            data={
                "periodo": "04/2025",
                "indice": "1.234,5678",
            },
            follow_redirects=False,
        )

        response = client.get("/contabilidad/indices-inflacion/")

    assert response.status_code == 200
    assert b'id="ec-indices-tabla"' in response.data
    assert b'data-row-periodo="202504"' in response.data
    assert b"04/2025" in response.data
    assert b"1.234,5678" in response.data


def test_post_indices_inflacion_invalido_vuelve_con_400_y_valores():
    """
    Valida manejo de errores de formulario sin romper la pantalla.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.post(
            "/contabilidad/indices-inflacion/",
            data={
                "periodo": "13/2025",
                "indice": "1.234,5678",
            },
            follow_redirects=False,
        )

    assert response.status_code == 400
    assert b'id="ec-indice-form"' in response.data
    assert b'value="13/2025"' in response.data
    assert b'value="1.234,5678"' in response.data
