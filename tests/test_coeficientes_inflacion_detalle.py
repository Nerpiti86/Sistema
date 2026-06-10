from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.coeficientes_inflacion_repository import (
    guardar_indice_inflacion,
    listar_coeficientes_inflacion_por_ejercicio_id,
)
from app.contabilidad.coeficientes_inflacion_service import (
    derivar_doce_periodos_ejercicio,
)
from app.contabilidad.ejercicios_contables_repository import (
    crear_ejercicio_contable,
)


def test_detalle_muestra_accion_y_estado_vacio_de_coeficientes():
    """
    Valida integracion visual inicial de coeficientes en detalle de ejercicio.

    La pantalla debe mostrar accion POST estable y estado vacio sin calcular
    datos en el template.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_abril()

        response = client.get("/contabilidad/ejercicios-contables/EJ2025/")

    assert response.status_code == 200
    assert b'id="ec-coef-card"' in response.data
    assert b'id="ec-coef-form"' in response.data
    assert b'id="ec-coef-generar"' in response.data
    assert b'data-action="generar_coeficientes_inflacion"' in response.data
    assert (
        b"/contabilidad/ejercicios-contables/EJ2025/"
        b"coeficientes-inflacion/generar/"
    ) in response.data
    assert b'id="ec-coef-vacio"' in response.data
    assert b"Sin coeficientes generados." in response.data


def test_post_generar_coeficientes_persiste_y_redirige_al_detalle():
    """
    Valida route POST de generacion sin SQL directo en route.

    El POST delega en service, persiste doce coeficientes y vuelve al detalle
    del mismo ejercicio contable.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        ejercicio = _crear_ejercicio_contable_abril()
        _cargar_indices_abril_a_marzo()
        guardar_indice_inflacion(202604, 20_000_000)

        response = client.post(
            "/contabilidad/ejercicios-contables/EJ2025/"
            "coeficientes-inflacion/generar/",
            follow_redirects=False,
        )

        coeficientes = listar_coeficientes_inflacion_por_ejercicio_id(
            ejercicio["id"]
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/ejercicios-contables/EJ2025/"
    )
    assert len(coeficientes) == 12
    assert coeficientes[0]["periodo_yyyymm"] == 202504
    assert coeficientes[-1]["periodo_yyyymm"] == 202603


def test_detalle_muestra_coeficientes_generados_con_formatos_argentinos():
    """
    Valida render de coeficientes ya preparados por service.

    El template solo muestra campos *_argentina recibidos en el contexto.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_abril()
        _cargar_indices_abril_a_marzo()
        guardar_indice_inflacion(202604, 20_000_000)

        client.post(
            "/contabilidad/ejercicios-contables/EJ2025/"
            "coeficientes-inflacion/generar/",
            follow_redirects=False,
        )

        response = client.get("/contabilidad/ejercicios-contables/EJ2025/")

    assert response.status_code == 200
    assert b'id="ec-coef-tabla"' in response.data
    assert b'data-row-periodo="202504"' in response.data
    assert b"04/2025" in response.data
    assert b"03/2026" in response.data
    assert b"04/2026" in response.data
    assert b"1.000,0000" in response.data
    assert b"2.000,0000" in response.data
    assert b"2,000000000000" in response.data


def test_post_generar_coeficientes_con_indices_faltantes_no_persiste():
    """
    Valida manejo de error cuando faltan indices de inicio.

    La route vuelve al detalle y el service evita guardar snapshots parciales.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        ejercicio = _crear_ejercicio_contable_abril()

        for periodo in derivar_doce_periodos_ejercicio("2025-04-01"):
            if periodo != 202505:
                guardar_indice_inflacion(periodo, 10_000_000)

        guardar_indice_inflacion(202604, 20_000_000)

        response = client.post(
            "/contabilidad/ejercicios-contables/EJ2025/"
            "coeficientes-inflacion/generar/",
            follow_redirects=False,
        )

        coeficientes = listar_coeficientes_inflacion_por_ejercicio_id(
            ejercicio["id"]
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/ejercicios-contables/EJ2025/"
    )
    assert coeficientes == []


def _crear_ejercicio_contable_abril():
    return crear_ejercicio_contable(
        {
            "codigo": "EJ2025",
            "nombre": "Ejercicio abril 2025 marzo 2026",
            "fecha_desde": "2025-04-01",
            "fecha_hasta": "2026-03-31",
            "estado": "ABIERTO",
            "activo": True,
            "fase_cierre": "ABIERTO",
            "bloqueado": False,
            "bloqueado_en": None,
            "observaciones_cierre": None,
            "es_primer_ejercicio": False,
        }
    )


def _cargar_indices_abril_a_marzo():
    for periodo in derivar_doce_periodos_ejercicio("2025-04-01"):
        guardar_indice_inflacion(periodo, 10_000_000)
