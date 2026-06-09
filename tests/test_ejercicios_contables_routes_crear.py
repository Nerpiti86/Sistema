from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_por_codigo,
)


def test_post_crear_ejercicio_contable_crea_registro_y_redirige_al_listado():
    """
    Valida route POST de alta de ejercicios_contables.

    La route no ejecuta SQL directo: recibe form, llama al service y redirige
    al listado. La verificacion de persistencia se hace con repository.
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
                "fecha_desde": "2026-01-01",
                "fecha_hasta": "2026-12-31",
                "estado": "ABIERTO",
                "activo": "1",
                "fase_cierre": "ABIERTO",
                "es_primer_ejercicio": "1",
                "observaciones_cierre": "Alta desde route",
            },
            follow_redirects=False,
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/ejercicios-contables/"
    )
    assert ejercicio_contable is not None
    assert ejercicio_contable["codigo"] == "EJ2026"
    assert ejercicio_contable["nombre"] == "Ejercicio 2026"
    assert ejercicio_contable["es_activo"] is True
    assert ejercicio_contable["observaciones_cierre"] == "Alta desde route"
    assert ejercicio_contable["es_primer_ejercicio_bool"] is True


def test_post_crear_ejercicio_contable_invalido_redirige_sin_crear_registro():
    """
    Valida manejo de error de la route POST.

    Ante datos invalidos, la route captura ValueError del service, flashea el
    mensaje y vuelve al listado sin crear registro.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.post(
            "/contabilidad/ejercicios-contables/nuevo/",
            data={
                "codigo": "",
                "nombre": "Ejercicio sin codigo",
                "fecha_desde": "2026-01-01",
                "fecha_hasta": "2026-12-31",
            },
            follow_redirects=False,
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/ejercicios-contables/"
    )
    assert ejercicio_contable is None


def test_post_crear_ejercicio_contable_no_rompe_listado_con_follow_redirects():
    """
    Valida integracion minima entre POST y pantalla existente.

    Aunque todavia no hay formulario HTML, el POST valido debe volver al
    listado y mostrar el ejercicio creado.
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
                "fecha_desde": "2026-01-01",
                "fecha_hasta": "2026-12-31",
                "estado": "ABIERTO",
                "fase_cierre": "ABIERTO",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"EJ2026" in response.data
    assert b"Ejercicio 2026" in response.data
    assert b'id="ec-tabla"' in response.data
