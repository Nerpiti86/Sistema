from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.ejercicios_contables_repository import crear_ejercicio_contable


def _crear_ejercicio_contable_para_detalle():
    return crear_ejercicio_contable(
        {
            "codigo": "EJ2026",
            "nombre": "Ejercicio 2026",
            "fecha_desde": "2026-01-01",
            "fecha_hasta": "2026-12-31",
            "estado": "ABIERTO",
            "activo": True,
            "fase_cierre": "ABIERTO",
            "bloqueado": False,
            "bloqueado_en": None,
            "observaciones_cierre": "Detalle de prueba",
            "es_primer_ejercicio": True,
        }
    )


def test_listado_muestra_accion_detalle_de_ejercicio_contable():
    """
    Valida acceso desde listado al detalle de ejercicios_contables.

    La accion usa data-action y data-row-codigo para trazabilidad sin depender
    de texto visual exclusivamente.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_para_detalle()

        response = client.get("/contabilidad/ejercicios-contables/")

    assert response.status_code == 200
    assert b'data-field="acciones"' in response.data
    assert b'data-action="ver_detalle_ejercicio_contable"' in response.data
    assert b'data-row-codigo="EJ2026"' in response.data
    assert b"/contabilidad/ejercicios-contables/EJ2026/" in response.data
    assert b"Detalle" in response.data


def test_get_detalle_ejercicio_contable_muestra_datos_reales():
    """
    Valida pantalla de detalle de solo lectura.

    El detalle lee un ejercicio puntual por codigo via service y muestra campos
    reales de la tabla ejercicios_contables.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_para_detalle()

        response = client.get("/contabilidad/ejercicios-contables/EJ2026/")

    assert response.status_code == 200
    assert b'id="ec-detalle"' in response.data
    assert b'data-query="obtener_contexto_detalle_ejercicio_contable"' in response.data
    assert b'data-row-codigo="EJ2026"' in response.data
    assert b"EJ2026" in response.data
    assert b"Ejercicio 2026" in response.data
    assert b"2026-01-01" in response.data
    assert b"2026-12-31" in response.data
    assert b"ABIERTO" in response.data
    assert b"Detalle de prueba" in response.data
    assert b'data-field="es_primer_ejercicio"' in response.data


def test_get_detalle_ejercicio_contable_inexistente_redirige_al_listado():
    """
    Valida manejo de inexistente en route detalle.

    Si el codigo no existe, la route no rompe y vuelve al listado con flash.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.get(
            "/contabilidad/ejercicios-contables/NOEXISTE/",
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/ejercicios-contables/"
    )
