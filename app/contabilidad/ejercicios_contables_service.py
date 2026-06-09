from datetime import datetime
from typing import Any

from app.contabilidad.ejercicios_contables_repository import (
    crear_ejercicio_contable,
    listar_ejercicios_contables,
    obtener_ejercicio_contable_activo,
    obtener_ejercicio_contable_por_codigo,
    obtener_ejercicio_contable_por_fecha,
    validar_ejercicio_contable_operable,
    validar_fecha_dentro_de_ejercicio_contable,
)
_ESTADOS_EJERCICIO_CONTABLE = ("ABIERTO", "CERRADO")
_FASES_CIERRE_EJERCICIO_CONTABLE = ("ABIERTO", "EN_CIERRE", "BLOQUEADO")


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



def crear_ejercicio_contable_desde_formulario(
    formulario_ejercicio_contable,
) -> dict[str, Any]:
    """
    Crea un ejercicio contable desde datos tipo formulario.

    Este service no ejecuta SQL directo. Normaliza y valida datos de entrada,
    y delega la persistencia en ejercicios_contables_repository.
    """
    datos_ejercicio_contable = _normalizar_formulario_crear_ejercicio_contable(
        formulario_ejercicio_contable
    )

    return crear_ejercicio_contable(datos_ejercicio_contable)


def obtener_contexto_detalle_ejercicio_contable(
    ejercicio_contable_codigo: str,
) -> dict[str, Any]:
    """
    Devuelve contexto chico para pantalla de detalle de ejercicios_contables.

    Este service no ejecuta SQL directo. La lectura puntual queda delegada al
    repository por codigo.
    """
    codigo_normalizado = str(ejercicio_contable_codigo or "").strip()

    if not codigo_normalizado:
        raise ValueError("El codigo de ejercicio contable es obligatorio.")

    ejercicio_contable = obtener_ejercicio_contable_por_codigo(codigo_normalizado)

    if ejercicio_contable is None:
        raise ValueError("No existe el ejercicio contable informado.")

    return {
        "ejercicio_contable": ejercicio_contable,
    }


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


def obtener_contexto_listado_ejercicios_contables() -> dict[str, Any]:
    """
    Devuelve contexto chico para pantalla de ejercicios_contables.

    La consulta base es listar_ejercicios_contables(). La tabla es chica y de
    contexto; no se cargan asientos, comprobantes ni movimientos asociados.
    """
    ejercicios_contables = listar_ejercicios_contables()

    ejercicio_contable_activo = None
    for ejercicio_contable in ejercicios_contables:
        if ejercicio_contable["es_activo"]:
            ejercicio_contable_activo = ejercicio_contable
            break

    return {
        "ejercicios_contables": ejercicios_contables,
        "cantidad_ejercicios_contables": len(ejercicios_contables),
        "ejercicio_contable_activo": ejercicio_contable_activo,
    }



def _normalizar_formulario_crear_ejercicio_contable(
    formulario_ejercicio_contable,
) -> dict[str, Any]:
    codigo = _normalizar_texto_obligatorio_ejercicio_contable(
        formulario_ejercicio_contable.get("codigo", ""),
        "El codigo de ejercicio contable es obligatorio.",
    )
    nombre = _normalizar_texto_obligatorio_ejercicio_contable(
        formulario_ejercicio_contable.get("nombre", ""),
        "El nombre de ejercicio contable es obligatorio.",
    )
    fecha_desde = _normalizar_fecha_iso_obligatoria_ejercicio_contable(
        formulario_ejercicio_contable.get("fecha_desde", ""),
        "La fecha desde de ejercicio contable es obligatoria.",
    )
    fecha_hasta = _normalizar_fecha_iso_obligatoria_ejercicio_contable(
        formulario_ejercicio_contable.get("fecha_hasta", ""),
        "La fecha hasta de ejercicio contable es obligatoria.",
    )

    if fecha_hasta < fecha_desde:
        raise ValueError("La fecha hasta no puede ser anterior a la fecha desde.")

    estado = _normalizar_opcion_ejercicio_contable(
        formulario_ejercicio_contable.get("estado", "ABIERTO"),
        _ESTADOS_EJERCICIO_CONTABLE,
        "El estado de ejercicio contable no es valido.",
    )
    fase_cierre = _normalizar_opcion_ejercicio_contable(
        formulario_ejercicio_contable.get("fase_cierre", "ABIERTO"),
        _FASES_CIERRE_EJERCICIO_CONTABLE,
        "La fase de cierre de ejercicio contable no es valida.",
    )

    activo = _normalizar_checkbox_ejercicio_contable(
        formulario_ejercicio_contable.get("activo")
    )
    bloqueado = _normalizar_checkbox_ejercicio_contable(
        formulario_ejercicio_contable.get("bloqueado")
    )
    es_primer_ejercicio = _normalizar_checkbox_ejercicio_contable(
        formulario_ejercicio_contable.get("es_primer_ejercicio")
    )

    if fase_cierre == "BLOQUEADO":
        bloqueado = True

    if bloqueado:
        fase_cierre = "BLOQUEADO"

    bloqueado_en = None
    if bloqueado:
        bloqueado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    observaciones_cierre = str(
        formulario_ejercicio_contable.get("observaciones_cierre", "") or ""
    ).strip()

    return {
        "codigo": codigo,
        "nombre": nombre,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "estado": estado,
        "activo": activo,
        "fase_cierre": fase_cierre,
        "bloqueado": bloqueado,
        "bloqueado_en": bloqueado_en,
        "observaciones_cierre": observaciones_cierre or None,
        "es_primer_ejercicio": es_primer_ejercicio,
    }


def _normalizar_texto_obligatorio_ejercicio_contable(
    valor,
    mensaje_error: str,
) -> str:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        raise ValueError(mensaje_error)

    return valor_normalizado


def _normalizar_fecha_iso_obligatoria_ejercicio_contable(
    valor,
    mensaje_error: str,
) -> str:
    fecha_normalizada = _normalizar_texto_obligatorio_ejercicio_contable(
        valor,
        mensaje_error,
    )

    try:
        datetime.strptime(fecha_normalizada, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("La fecha debe tener formato YYYY-MM-DD.") from exc

    return fecha_normalizada


def _normalizar_opcion_ejercicio_contable(
    valor,
    opciones_validas: tuple[str, ...],
    mensaje_error: str,
) -> str:
    valor_normalizado = str(valor or "").strip()

    if valor_normalizado not in opciones_validas:
        raise ValueError(mensaje_error)

    return valor_normalizado


def _normalizar_checkbox_ejercicio_contable(valor) -> bool:
    return str(valor or "").strip() in {"1", "on", "true", "True", "SI", "Si"}


def _validar_ejercicio_contable_activo_para_operacion(
    ejercicio_contable: dict[str, Any],
) -> bool:
    """Valida que el ejercicio contable informado sea el activo operativo."""
    if not ejercicio_contable.get("es_activo"):
        raise ValueError(
            "El ejercicio contable informado no esta activo para operaciones."
        )

    return True
