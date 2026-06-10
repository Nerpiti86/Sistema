import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.coeficientes_inflacion_repository import (
    guardar_indice_inflacion,
    listar_coeficientes_inflacion_por_ejercicio_id,
)
from app.contabilidad.coeficientes_inflacion_service import (
    calcular_coeficiente_inflacion,
    derivar_doce_periodos_ejercicio,
    generar_coeficientes_inflacion_ejercicio,
    obtener_contexto_coeficientes_inflacion_ejercicio,
    sumar_meses_periodo_yyyymm,
)
from app.contabilidad.ejercicios_contables_repository import (
    crear_ejercicio_contable,
)


def test_service_deriva_doce_periodos_desde_inicio_no_enero():
    """Valida periodos mensuales aun cuando el ejercicio no inicia en enero."""
    periodos = derivar_doce_periodos_ejercicio("2025-04-01")

    assert periodos == [
        202504,
        202505,
        202506,
        202507,
        202508,
        202509,
        202510,
        202511,
        202512,
        202601,
        202602,
        202603,
    ]


def test_service_suma_meses_periodo_con_cambio_de_anio():
    """Valida aritmetica de periodos YYYYMM sin fechas ni floats."""
    assert sumar_meses_periodo_yyyymm(202512, 1) == 202601
    assert sumar_meses_periodo_yyyymm(202504, 11) == 202603


def test_service_calcula_coeficiente_con_enteros():
    """Valida calculo de coeficiente con escala 12 sin float."""
    assert calcular_coeficiente_inflacion(
        10_000_000,
        20_000_000,
    ) == 2_000_000_000_000

    assert calcular_coeficiente_inflacion(
        78_641_257,
        101_213_715,
    ) == 1_287_030_737_568


def test_service_genera_doce_coeficientes_con_ultimo_indice_cargado():
    """Valida generacion completa usando ultimo indice como cierre comun."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_abril()
        _cargar_indices_abril_a_marzo()
        guardar_indice_inflacion(202604, 20_000_000)

        coeficientes = generar_coeficientes_inflacion_ejercicio("EJ2025")
        persistidos = listar_coeficientes_inflacion_por_ejercicio_id(
            coeficientes[0]["ejercicio_id"]
        )

    assert len(coeficientes) == 12
    assert len(persistidos) == 12
    assert coeficientes[0]["periodo_yyyymm"] == 202504
    assert coeficientes[-1]["periodo_yyyymm"] == 202603
    assert {
        coeficiente["indice_cierre_periodo_yyyymm"]
        for coeficiente in coeficientes
    } == {202604}
    assert coeficientes[0]["coeficiente_1000000000000"] == 2_000_000_000_000


def test_service_informa_indices_faltantes_sin_persistir_snapshot():
    """Valida que no se generen coeficientes si falta algun periodo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        ejercicio = _crear_ejercicio_contable_abril()

        for periodo in derivar_doce_periodos_ejercicio("2025-04-01"):
            if periodo != 202505:
                guardar_indice_inflacion(periodo, 10_000_000)

        guardar_indice_inflacion(202604, 20_000_000)

        with pytest.raises(ValueError) as exc_info:
            generar_coeficientes_inflacion_ejercicio("EJ2025")

        persistidos = listar_coeficientes_inflacion_por_ejercicio_id(
            ejercicio["id"]
        )

    assert "05/2025" in str(exc_info.value)
    assert persistidos == []


def test_service_rechaza_generar_sin_indices_cargados():
    """Valida error claro cuando no hay indice de cierre disponible."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_abril()

        with pytest.raises(ValueError) as exc_info:
            generar_coeficientes_inflacion_ejercicio("EJ2025")

    assert "No existen indices de inflacion cargados." in str(exc_info.value)


def test_service_prepara_contexto_para_pantalla_con_formatos_argentinos():
    """Valida que el template reciba periodos e importes ya formateados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_abril()
        _cargar_indices_abril_a_marzo()
        guardar_indice_inflacion(202604, 20_000_000)

        generar_coeficientes_inflacion_ejercicio("EJ2025")
        contexto = obtener_contexto_coeficientes_inflacion_ejercicio("EJ2025")

    assert contexto["cantidad_coeficientes_inflacion"] == 12
    assert contexto["tiene_coeficientes_inflacion"] is True
    assert contexto["coeficientes_inflacion"][0]["periodo_argentina"] == "04/2025"
    assert (
        contexto["coeficientes_inflacion"][0]["indice_inicio_argentina"]
        == "1.000,0000"
    )
    assert (
        contexto["coeficientes_inflacion"][0]["indice_cierre_argentina"]
        == "2.000,0000"
    )
    assert (
        contexto["coeficientes_inflacion"][0]["coeficiente_argentina"]
        == "2,000000000000"
    )
    assert contexto["coeficientes_inflacion"][0]["calculado_en_argentina"]


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
