from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_por_codigo,
)


def test_listado_muestra_boton_nuevo_ejercicio_contable():
    """
    Valida acceso visual al formulario de alta.

    El boton usa ID corto ec-nuevo y data-action para mantener trazabilidad.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/")

    assert response.status_code == 200
    assert b'id="ec-nuevo"' in response.data
    assert b'data-action="crear_ejercicio_contable"' in response.data
    assert b"/contabilidad/ejercicios-contables/nuevo/" in response.data


def test_get_formulario_crear_ejercicio_contable_muestra_campos_reales():
    """
    Valida formulario GET de alta de ejercicios_contables.

    El formulario usa IDs cortos y data-field con nombres reales de columnas.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/nuevo/")

    assert response.status_code == 200
    assert b'id="ec-form"' in response.data
    assert b'id="ec-codigo"' in response.data
    assert b'id="ec-nombre"' in response.data
    assert b'id="ec-fecha-desde"' in response.data
    assert b'id="ec-fecha-hasta"' in response.data
    assert b'placeholder="DD/MM/AAAA"' in response.data
    assert b'type="date"' not in response.data
    assert b'id="ec-estado"' in response.data
    assert b'id="ec-fase-cierre"' in response.data
    assert b'id="ec-activo"' in response.data
    assert b'id="ec-bloqueado"' in response.data
    assert b'id="ec-es-primer-ejercicio"' in response.data
    assert b'id="ec-observaciones-cierre"' in response.data
    assert b'data-table="ejercicios_contables"' in response.data
    assert b'data-field="es_primer_ejercicio"' in response.data


def test_post_desde_formulario_crear_ejercicio_contable_crea_y_vuelve_al_listado():
    """
    Valida integracion visual minima del formulario con el POST existente.

    El submit del formulario usa la route POST ya creada en el paso anterior.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.post(
            "/contabilidad/ejercicios-contables/nuevo/",
            data={
                "codigo": "EJ2026",
                "nombre": "Ejercicio 2026",
                "fecha_desde": "01/01/2026",
                "fecha_hasta": "31/12/2026",
                "estado": "ABIERTO",
                "fase_cierre": "ABIERTO",
                "activo": "1",
                "es_primer_ejercicio": "1",
                "observaciones_cierre": "Alta desde formulario",
            },
            follow_redirects=True,
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert response.status_code == 200
    assert b"EJ2026" in response.data
    assert ejercicio_contable is not None
    assert ejercicio_contable["observaciones_cierre"] == "Alta desde formulario"
