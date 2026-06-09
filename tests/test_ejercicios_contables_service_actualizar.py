import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.ejercicios_contables_repository import (
    crear_ejercicio_contable,
    obtener_ejercicio_contable_por_codigo,
)
from app.contabilidad.ejercicios_contables_service import (
    actualizar_ejercicio_contable_desde_formulario,
)


def _crear_ejercicio_contable_base(
    codigo="EJ2026",
    activo=False,
    bloqueado=False,
    bloqueado_en=None,
):
    return crear_ejercicio_contable(
        {
            "codigo": codigo,
            "nombre": f"Ejercicio {codigo}",
            "fecha_desde": "2026-01-01",
            "fecha_hasta": "2026-12-31",
            "estado": "ABIERTO",
            "activo": activo,
            "fase_cierre": "BLOQUEADO" if bloqueado else "ABIERTO",
            "bloqueado": bloqueado,
            "bloqueado_en": bloqueado_en,
            "observaciones_cierre": None,
            "es_primer_ejercicio": False,
        }
    )


def test_actualizar_ejercicio_contable_desde_formulario_modifica_campos_mutables():
    """
    Valida service update desde formulario.

    El service no cambia codigo: normaliza campos mutables y delega el UPDATE
    al repository.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_base("EJ2026", activo=True)

        actualizado = actualizar_ejercicio_contable_desde_formulario(
            " EJ2026 ",
            {
                "nombre": " Ejercicio 2026 actualizado ",
                "fecha_desde": "01/02/2026",
                "fecha_hasta": "30/11/2026",
                "estado": "CERRADO",
                "fase_cierre": "ABIERTO",
                "observaciones_cierre": " Observacion service ",
                "es_primer_ejercicio": "1",
            },
        )

        recuperado = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert actualizado["codigo"] == "EJ2026"
    assert actualizado["nombre"] == "Ejercicio 2026 actualizado"
    assert actualizado["fecha_desde"] == "2026-02-01"
    assert actualizado["fecha_hasta"] == "2026-11-30"
    assert actualizado["estado_codigo"] == "CERRADO"
    assert actualizado["fase_cierre_codigo"] == "ABIERTO"
    assert actualizado["es_activo"] is False
    assert actualizado["esta_bloqueado"] is False
    assert actualizado["bloqueado_en"] is None
    assert actualizado["observaciones_cierre"] == "Observacion service"
    assert actualizado["es_primer_ejercicio_bool"] is True
    assert actualizado["actualizado_en"] is not None
    assert recuperado == actualizado


def test_actualizar_ejercicio_contable_desde_formulario_bloquea_y_genera_fecha():
    """
    Valida normalizacion de bloqueo desde service.

    Si el formulario pide BLOQUEADO, el service fuerza bloqueado=True y asigna
    fecha de bloqueo cuando no habia una previa.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_base("EJ2026")

        actualizado = actualizar_ejercicio_contable_desde_formulario(
            "EJ2026",
            {
                "nombre": "Ejercicio 2026",
                "fecha_desde": "01/01/2026",
                "fecha_hasta": "31/12/2026",
                "estado": "ABIERTO",
                "fase_cierre": "BLOQUEADO",
            },
        )

    assert actualizado["esta_bloqueado"] is True
    assert actualizado["fase_cierre_codigo"] == "BLOQUEADO"
    assert actualizado["bloqueado_en"] is not None


def test_actualizar_ejercicio_contable_desde_formulario_conserva_fecha_bloqueo_existente():
    """
    Valida que service no pise bloqueado_en si el ejercicio ya estaba bloqueado.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_base(
            "EJ2026",
            bloqueado=True,
            bloqueado_en="2026-06-01 10:00:00",
        )

        actualizado = actualizar_ejercicio_contable_desde_formulario(
            "EJ2026",
            {
                "nombre": "Ejercicio 2026 bloqueado",
                "fecha_desde": "01/01/2026",
                "fecha_hasta": "31/12/2026",
                "estado": "ABIERTO",
                "fase_cierre": "BLOQUEADO",
                "bloqueado": "1",
            },
        )

    assert actualizado["esta_bloqueado"] is True
    assert actualizado["bloqueado_en"] == "2026-06-01 10:00:00"


def test_actualizar_ejercicio_contable_desde_formulario_desbloquea_y_limpia_fecha():
    """
    Valida desbloqueo desde formulario.

    Cuando el formulario vuelve a fase ABIERTO sin check bloqueado, el service
    limpia bloqueado_en.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_base(
            "EJ2026",
            bloqueado=True,
            bloqueado_en="2026-06-01 10:00:00",
        )

        actualizado = actualizar_ejercicio_contable_desde_formulario(
            "EJ2026",
            {
                "nombre": "Ejercicio 2026 abierto",
                "fecha_desde": "01/01/2026",
                "fecha_hasta": "31/12/2026",
                "estado": "ABIERTO",
                "fase_cierre": "ABIERTO",
            },
        )

    assert actualizado["esta_bloqueado"] is False
    assert actualizado["fase_cierre_codigo"] == "ABIERTO"
    assert actualizado["bloqueado_en"] is None


def test_actualizar_ejercicio_contable_desde_formulario_rechaza_inexistente():
    """
    Valida que service rechace codigo inexistente antes de delegar update.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe"):
            actualizar_ejercicio_contable_desde_formulario(
                "NOEXISTE",
                {
                    "nombre": "No existe",
                    "fecha_desde": "01/01/2026",
                    "fecha_hasta": "31/12/2026",
                    "estado": "ABIERTO",
                    "fase_cierre": "ABIERTO",
                },
            )


def test_actualizar_ejercicio_contable_desde_formulario_rechaza_estado_invalido():
    """
    Valida que service mantenga contrato de opciones validas.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_base("EJ2026")

        with pytest.raises(ValueError, match="estado"):
            actualizar_ejercicio_contable_desde_formulario(
                "EJ2026",
                {
                    "nombre": "Ejercicio 2026",
                    "fecha_desde": "01/01/2026",
                    "fecha_hasta": "31/12/2026",
                    "estado": "INVALIDO",
                    "fase_cierre": "ABIERTO",
                },
            )
