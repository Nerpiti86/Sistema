import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.ejercicios_contables_repository import (
    actualizar_ejercicio_contable_por_codigo,
    crear_ejercicio_contable,
    obtener_ejercicio_contable_por_codigo,
)


def _datos_base_ejercicio_contable(codigo, activo=False):
    return {
        "codigo": codigo,
        "nombre": f"Ejercicio {codigo}",
        "fecha_desde": "2026-01-01",
        "fecha_hasta": "2026-12-31",
        "estado": "ABIERTO",
        "activo": activo,
        "fase_cierre": "ABIERTO",
        "bloqueado": False,
        "bloqueado_en": None,
        "observaciones_cierre": None,
        "es_primer_ejercicio": False,
    }


def test_actualizar_ejercicio_contable_modifica_campos_mutables_y_no_codigo():
    """
    Valida update repository de ejercicios_contables.

    El codigo se usa como identificador estable; el update solo modifica campos
    mutables y registra actualizado_en.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_ejercicio_contable(_datos_base_ejercicio_contable("EJ2026", activo=True))

        actualizado = actualizar_ejercicio_contable_por_codigo(
            " EJ2026 ",
            {
                "nombre": "Ejercicio 2026 actualizado",
                "fecha_desde": "2026-02-01",
                "fecha_hasta": "2026-11-30",
                "estado": "CERRADO",
                "activo": False,
                "fase_cierre": "BLOQUEADO",
                "bloqueado": True,
                "bloqueado_en": "2026-12-01 10:30:00",
                "observaciones_cierre": "Cierre actualizado",
                "es_primer_ejercicio": True,
            },
        )

        recuperado = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert actualizado["codigo"] == "EJ2026"
    assert actualizado["nombre"] == "Ejercicio 2026 actualizado"
    assert actualizado["fecha_desde"] == "2026-02-01"
    assert actualizado["fecha_hasta"] == "2026-11-30"
    assert actualizado["estado_codigo"] == "CERRADO"
    assert actualizado["es_activo"] is False
    assert actualizado["fase_cierre_codigo"] == "BLOQUEADO"
    assert actualizado["esta_bloqueado"] is True
    assert actualizado["bloqueado_en"] == "2026-12-01 10:30:00"
    assert actualizado["observaciones_cierre"] == "Cierre actualizado"
    assert actualizado["es_primer_ejercicio_bool"] is True
    assert actualizado["actualizado_en"] is not None
    assert recuperado == actualizado


def test_actualizar_ejercicio_contable_inexistente_rechaza():
    """
    Valida que repository no haga update silencioso sobre codigo inexistente.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe"):
            actualizar_ejercicio_contable_por_codigo(
                "NOEXISTE",
                {
                    "nombre": "No existe",
                    "fecha_desde": "2026-01-01",
                    "fecha_hasta": "2026-12-31",
                    "estado": "ABIERTO",
                    "activo": False,
                    "fase_cierre": "ABIERTO",
                    "bloqueado": False,
                    "bloqueado_en": None,
                    "observaciones_cierre": None,
                    "es_primer_ejercicio": False,
                },
            )


def test_actualizar_ejercicio_contable_rechaza_fechas_invertidas():
    """
    Valida regla minima de rango antes de ejecutar UPDATE.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_ejercicio_contable(_datos_base_ejercicio_contable("EJ2026"))

        with pytest.raises(ValueError, match="fecha hasta"):
            actualizar_ejercicio_contable_por_codigo(
                "EJ2026",
                {
                    "nombre": "Ejercicio 2026",
                    "fecha_desde": "2026-12-31",
                    "fecha_hasta": "2026-01-01",
                    "estado": "ABIERTO",
                    "activo": False,
                    "fase_cierre": "ABIERTO",
                    "bloqueado": False,
                    "bloqueado_en": None,
                    "observaciones_cierre": None,
                    "es_primer_ejercicio": False,
                },
            )


def test_actualizar_ejercicio_contable_rechaza_segundo_activo_por_indice_unico():
    """
    Valida que el update respete el indice unico parcial de activo.

    Si ya existe un ejercicio activo, no se puede activar otro registro.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_ejercicio_contable(_datos_base_ejercicio_contable("EJ2026", activo=True))
        crear_ejercicio_contable(_datos_base_ejercicio_contable("EJ2027", activo=False))

        with pytest.raises(ValueError, match="No se pudo actualizar"):
            actualizar_ejercicio_contable_por_codigo(
                "EJ2027",
                {
                    "nombre": "Ejercicio 2027",
                    "fecha_desde": "2027-01-01",
                    "fecha_hasta": "2027-12-31",
                    "estado": "ABIERTO",
                    "activo": True,
                    "fase_cierre": "ABIERTO",
                    "bloqueado": False,
                    "bloqueado_en": None,
                    "observaciones_cierre": None,
                    "es_primer_ejercicio": False,
                },
            )

        ejercicio_2027 = obtener_ejercicio_contable_por_codigo("EJ2027")

    assert ejercicio_2027["es_activo"] is False
