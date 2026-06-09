import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_por_codigo,
)
from app.contabilidad.ejercicios_contables_service import (
    crear_ejercicio_contable_desde_formulario,
)


def test_crear_ejercicio_contable_desde_formulario_persiste_campos_reales():
    """
    Valida alta desde service con datos tipo formulario.

    El service normaliza datos y delega la persistencia al repository.
    No ejecuta SQL directo.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        ejercicio_contable_creado = crear_ejercicio_contable_desde_formulario(
            {
                "codigo": " EJ2026 ",
                "nombre": " Ejercicio 2026 ",
                "fecha_desde": "01/01/2026",
                "fecha_hasta": "31/12/2026",
                "estado": "ABIERTO",
                "activo": "1",
                "fase_cierre": "ABIERTO",
                "bloqueado": "",
                "observaciones_cierre": " Alta desde service ",
                "es_primer_ejercicio": "on",
            }
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert ejercicio_contable_creado["codigo"] == "EJ2026"
    assert ejercicio_contable["nombre"] == "Ejercicio 2026"
    assert ejercicio_contable["fecha_desde"] == "2026-01-01"
    assert ejercicio_contable["fecha_hasta"] == "2026-12-31"
    assert ejercicio_contable["es_activo"] is True
    assert ejercicio_contable["esta_bloqueado"] is False
    assert ejercicio_contable["observaciones_cierre"] == "Alta desde service"
    assert ejercicio_contable["es_primer_ejercicio_bool"] is True


def test_crear_ejercicio_contable_desde_formulario_aplica_defaults_sanos():
    """
    Valida defaults de alta cuando el formulario no envia checks ni selects.

    El service completa estado ABIERTO, fase_cierre ABIERTO y flags falsos.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_ejercicio_contable_desde_formulario(
            {
                "codigo": "EJ2026",
                "nombre": "Ejercicio 2026",
                "fecha_desde": "01/01/2026",
                "fecha_hasta": "31/12/2026",
            }
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert ejercicio_contable["estado_codigo"] == "ABIERTO"
    assert ejercicio_contable["fase_cierre_codigo"] == "ABIERTO"
    assert ejercicio_contable["es_activo"] is False
    assert ejercicio_contable["esta_bloqueado"] is False
    assert ejercicio_contable["observaciones_cierre"] is None
    assert ejercicio_contable["es_primer_ejercicio_bool"] is False


def test_crear_ejercicio_contable_desde_formulario_bloquea_por_fase_bloqueado():
    """
    Valida coherencia entre fase_cierre BLOQUEADO y bloqueado.

    Si el formulario indica fase BLOQUEADO, el service marca bloqueado y
    registra bloqueado_en antes de delegar al repository.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_ejercicio_contable_desde_formulario(
            {
                "codigo": "EJ2026",
                "nombre": "Ejercicio 2026",
                "fecha_desde": "01/01/2026",
                "fecha_hasta": "31/12/2026",
                "fase_cierre": "BLOQUEADO",
            }
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert ejercicio_contable["fase_cierre_codigo"] == "BLOQUEADO"
    assert ejercicio_contable["esta_bloqueado"] is True
    assert ejercicio_contable["bloqueado_en"] is not None


def test_crear_ejercicio_contable_desde_formulario_rechaza_fechas_invertidas():
    """
    Valida regla de periodo antes de llamar al repository.

    El service no permite fecha_hasta anterior a fecha_desde.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="fecha hasta"):
            crear_ejercicio_contable_desde_formulario(
                {
                    "codigo": "EJ2026",
                    "nombre": "Ejercicio 2026",
                    "fecha_desde": "31/12/2026",
                    "fecha_hasta": "01/01/2026",
                }
            )


def test_crear_ejercicio_contable_desde_formulario_rechaza_estado_invalido():
    """
    Valida catalogo permitido para estado de ejercicios_contables.

    Estados admitidos: ABIERTO y CERRADO.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="estado"):
            crear_ejercicio_contable_desde_formulario(
                {
                    "codigo": "EJ2026",
                    "nombre": "Ejercicio 2026",
                    "fecha_desde": "01/01/2026",
                    "fecha_hasta": "31/12/2026",
                    "estado": "INVALIDO",
                }
            )
