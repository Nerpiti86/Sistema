from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.ejercicios_contables_repository import (
    crear_ejercicio_contable,
    obtener_ejercicio_contable_por_codigo,
)


def _crear_ejercicio_contable_para_editar():
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
            "observaciones_cierre": "Original",
            "es_primer_ejercicio": True,
        }
    )


def test_detalle_muestra_boton_editar_ejercicio_contable():
    """
    Valida acceso visual a edicion desde detalle.

    El boton Editar vive en el detalle, no en el listado, para no exponer una
    accion sensible como accion primaria de la tabla.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_para_editar()

        response = client.get("/contabilidad/ejercicios-contables/EJ2026/")

    assert response.status_code == 200
    assert b'id="ec-editar"' in response.data
    assert b'data-action="editar_ejercicio_contable"' in response.data
    assert b'data-row-codigo="EJ2026"' in response.data
    assert b"/contabilidad/ejercicios-contables/EJ2026/editar/" in response.data


def test_get_formulario_editar_muestra_datos_actuales():
    """
    Valida GET de formulario de edicion.

    El formulario reutiliza el template de alta, pero en modo editar, con codigo
    de solo lectura y action POST a la route de update.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_para_editar()

        response = client.get("/contabilidad/ejercicios-contables/EJ2026/editar/")

    assert response.status_code == 200
    assert b'id="ec-form-editar"' in response.data
    assert b"Editar ejercicio contable EJ2026" in response.data
    assert b'data-action="editar_ejercicio_contable"' in response.data
    assert b'action="/contabilidad/ejercicios-contables/EJ2026/editar/"' in response.data
    assert b'id="ec-codigo"' in response.data
    assert b'value="EJ2026"' in response.data
    assert b"readonly" in response.data
    assert b'value="Ejercicio 2026"' in response.data
    assert b'value="2026-01-01"' in response.data
    assert b'value="2026-12-31"' in response.data
    assert b"Original" in response.data
    assert b"Guardar cambios" in response.data


def test_post_editar_actualiza_ejercicio_contable_y_redirige_al_detalle():
    """
    Valida POST de edicion end-to-end.

    La route llama al service update, persiste por repository y vuelve al
    detalle del mismo codigo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_para_editar()

        response = client.post(
            "/contabilidad/ejercicios-contables/EJ2026/editar/",
            data={
                "nombre": "Ejercicio 2026 editado",
                "fecha_desde": "2026-02-01",
                "fecha_hasta": "2026-11-30",
                "estado": "CERRADO",
                "fase_cierre": "ABIERTO",
                "observaciones_cierre": "Editado desde route",
            },
            follow_redirects=False,
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/ejercicios-contables/EJ2026/"
    )
    assert ejercicio_contable["codigo"] == "EJ2026"
    assert ejercicio_contable["nombre"] == "Ejercicio 2026 editado"
    assert ejercicio_contable["fecha_desde"] == "2026-02-01"
    assert ejercicio_contable["fecha_hasta"] == "2026-11-30"
    assert ejercicio_contable["estado_codigo"] == "CERRADO"
    assert ejercicio_contable["es_activo"] is False
    assert ejercicio_contable["observaciones_cierre"] == "Editado desde route"
    assert ejercicio_contable["actualizado_en"] is not None


def test_post_editar_invalido_redirige_a_formulario_y_no_actualiza():
    """
    Valida manejo de error de POST editar.

    Si el service rechaza datos invalidos, la route vuelve al formulario de
    edicion y no modifica el registro.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_para_editar()

        response = client.post(
            "/contabilidad/ejercicios-contables/EJ2026/editar/",
            data={
                "nombre": "No debe persistir",
                "fecha_desde": "2026-12-31",
                "fecha_hasta": "2026-01-01",
                "estado": "ABIERTO",
                "fase_cierre": "ABIERTO",
            },
            follow_redirects=False,
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/ejercicios-contables/EJ2026/editar/"
    )
    assert ejercicio_contable["nombre"] == "Ejercicio 2026"
    assert ejercicio_contable["fecha_desde"] == "2026-01-01"
    assert ejercicio_contable["fecha_hasta"] == "2026-12-31"
    assert ejercicio_contable["actualizado_en"] is None
