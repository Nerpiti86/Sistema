from typing import Any

from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_activo,
    obtener_ejercicio_contable_por_codigo,
    obtener_ejercicio_contable_por_fecha,
    validar_ejercicio_contable_operable,
    validar_fecha_dentro_de_ejercicio_contable,
)


def resolver_ejercicio_contable_para_fecha_operacion(
    fecha_operacion_iso: str,
) -> dict[str, Any]:
    """
    Resuelve el ejercicio contable activo y operable para una fecha de operacion.

    Este service no ejecuta SQL directo. Toda lectura puntual queda en el
    repository identificable de ejercicios_contables.
    """
    ejercicio_contable = obtener_ejercicio_contable_por_fecha(fecha_operacion_iso)

    if ejercicio_contable is None:
        raise ValueError("No existe ejercicio contable activo para la fecha informada.")

    _validar_ejercicio_contable_activo_para_operacion(ejercicio_contable)
    validar_ejercicio_contable_operable(ejercicio_contable["codigo"])

    return ejercicio_contable


def validar_operacion_en_ejercicio_contable(
    fecha_operacion_iso: str,
    ejercicio_contable_codigo: str,
) -> bool:
    """
    Valida que una operacion pueda imputarse al ejercicio contable informado.

    Reglas:
    - el ejercicio contable debe existir
    - debe estar activo
    - la fecha debe pertenecer al rango del ejercicio
    - el ejercicio debe estar operable
    """
    ejercicio_contable = obtener_ejercicio_contable_por_codigo(
        ejercicio_contable_codigo
    )

    if ejercicio_contable is None:
        raise ValueError("No existe el ejercicio contable informado.")

    _validar_ejercicio_contable_activo_para_operacion(ejercicio_contable)

    validar_fecha_dentro_de_ejercicio_contable(
        fecha_operacion_iso,
        ejercicio_contable["codigo"],
    )

    validar_ejercicio_contable_operable(ejercicio_contable["codigo"])

    return True


def obtener_contexto_ejercicio_contable_activo() -> dict[str, Any]:
    """
    Devuelve un contexto minimo del ejercicio contable activo.

    No devuelve listados completos ni datos operativos grandes.
    """
    ejercicio_contable_activo = obtener_ejercicio_contable_activo()

    return {
        "ejercicio_contable_activo": ejercicio_contable_activo,
        "ejercicio_contable_codigo": ejercicio_contable_activo["codigo"],
        "ejercicio_contable_nombre": ejercicio_contable_activo["nombre"],
        "ejercicio_contable_fecha_desde": ejercicio_contable_activo["fecha_desde"],
        "ejercicio_contable_fecha_hasta": ejercicio_contable_activo["fecha_hasta"],
        "ejercicio_contable_estado": ejercicio_contable_activo["estado_codigo"],
        "ejercicio_contable_fase_cierre": ejercicio_contable_activo[
            "fase_cierre_codigo"
        ],
        "ejercicio_contable_bloqueado": ejercicio_contable_activo[
            "esta_bloqueado"
        ],
    }


def _validar_ejercicio_contable_activo_para_operacion(
    ejercicio_contable: dict[str, Any],
) -> bool:
    """Valida que el ejercicio contable informado sea el activo operativo."""
    if not ejercicio_contable.get("es_activo"):
        raise ValueError(
            "El ejercicio contable informado no esta activo para operaciones."
        )

    return True
