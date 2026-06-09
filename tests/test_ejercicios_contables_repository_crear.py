import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.ejercicios_contables_repository import (
    crear_ejercicio_contable,
    listar_ejercicios_contables,
    obtener_ejercicio_contable_por_codigo,
)


def _datos_ejercicio_contable_para_crear(
    codigo,
    fecha_desde="2026-01-01",
    fecha_hasta="2026-12-31",
    activo=False,
    bloqueado=False,
    es_primer_ejercicio=False,
):
    """
    Arma datos con nombres reales de columnas de ejercicios_contables.

    El objetivo del test es validar el repository puro: no intervienen
    service, routes, templates ni formularios HTML.
    """
    return {
        "codigo": codigo,
        "nombre": f"Ejercicio {codigo}",
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "estado": "ABIERTO",
        "activo": activo,
        "fase_cierre": "ABIERTO",
        "bloqueado": bloqueado,
        "bloqueado_en": None,
        "observaciones_cierre": "Alta repository test",
        "es_primer_ejercicio": es_primer_ejercicio,
    }


def test_crear_ejercicio_contable_persiste_campos_reales_de_tabla():
    """
    Valida que crear_ejercicio_contable inserte las columnas reales.

    Incluye campos de control contable como activo, bloqueado,
    observaciones_cierre y es_primer_ejercicio.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        ejercicio_contable_creado = crear_ejercicio_contable(
            _datos_ejercicio_contable_para_crear(
                "EJ2026",
                activo=True,
                es_primer_ejercicio=True,
            )
        )

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ2026")

    assert ejercicio_contable_creado["codigo"] == "EJ2026"
    assert ejercicio_contable["codigo"] == "EJ2026"
    assert ejercicio_contable["nombre"] == "Ejercicio EJ2026"
    assert ejercicio_contable["fecha_desde"] == "2026-01-01"
    assert ejercicio_contable["fecha_hasta"] == "2026-12-31"
    assert ejercicio_contable["estado_codigo"] == "ABIERTO"
    assert ejercicio_contable["fase_cierre_codigo"] == "ABIERTO"
    assert ejercicio_contable["es_activo"] is True
    assert ejercicio_contable["esta_bloqueado"] is False
    assert ejercicio_contable["observaciones_cierre"] == "Alta repository test"
    assert ejercicio_contable["es_primer_ejercicio_bool"] is True


def test_crear_ejercicio_contable_rechaza_codigo_duplicado():
    """
    Valida que repository respete UNIQUE de ejercicios_contables.codigo.

    La BD rechaza el duplicado y el repository traduce el error a ValueError.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_ejercicio_contable(
            _datos_ejercicio_contable_para_crear("EJ2026")
        )

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_ejercicio_contable(
                _datos_ejercicio_contable_para_crear("EJ2026")
            )


def test_crear_ejercicio_contable_rechaza_segundo_activo_por_indice_unico():
    """
    Valida ux_ejercicios_contables_activo_unico sin inventar automatismos.

    En este paso el repository no desactiva ejercicios anteriores. Si se
    intenta insertar un segundo activo, la BD debe rechazar la operacion.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_ejercicio_contable(
            _datos_ejercicio_contable_para_crear(
                "EJ2025",
                fecha_desde="2025-01-01",
                fecha_hasta="2025-12-31",
                activo=True,
            )
        )

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_ejercicio_contable(
                _datos_ejercicio_contable_para_crear(
                    "EJ2026",
                    fecha_desde="2026-01-01",
                    fecha_hasta="2026-12-31",
                    activo=True,
                )
            )


def test_crear_ejercicio_contable_rechaza_fecha_hasta_anterior_a_fecha_desde():
    """
    Valida regla minima de rango antes de insertar en ejercicios_contables.

    Evita guardar ejercicios con periodo invertido desde el repository.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="fecha hasta"):
            crear_ejercicio_contable(
                _datos_ejercicio_contable_para_crear(
                    "EJ2026",
                    fecha_desde="2026-12-31",
                    fecha_hasta="2026-01-01",
                )
            )


def test_crear_ejercicio_contable_no_impone_unico_es_primer_ejercicio():
    """
    Documenta el contrato actual de es_primer_ejercicio.

    La migracion no define indice unico para es_primer_ejercicio. Por eso este
    repository solo persiste el valor recibido y no inventa una regla global.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_ejercicio_contable(
            _datos_ejercicio_contable_para_crear(
                "EJ2025",
                fecha_desde="2025-01-01",
                fecha_hasta="2025-12-31",
                es_primer_ejercicio=True,
            )
        )
        crear_ejercicio_contable(
            _datos_ejercicio_contable_para_crear(
                "EJ2026",
                fecha_desde="2026-01-01",
                fecha_hasta="2026-12-31",
                es_primer_ejercicio=True,
            )
        )

        ejercicios_contables = listar_ejercicios_contables()

    primeros = [
        ejercicio_contable
        for ejercicio_contable in ejercicios_contables
        if ejercicio_contable["es_primer_ejercicio_bool"]
    ]

    assert len(primeros) == 2
