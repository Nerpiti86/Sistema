from typing import Any

from app.shared.monedas_repository import (
    actualizar_moneda_por_codigo,
    cambiar_estado_moneda,
    crear_moneda,
    listar_monedas,
    listar_monedas_activas,
    obtener_moneda_por_codigo,
    validar_moneda_activa,
)


def obtener_contexto_listado_monedas() -> dict[str, Any]:
    """
    Devuelve contexto chico del maestro monedas.

    Este service no ejecuta SQL directo. La lectura queda delegada al
    repository transversal de monedas.
    """
    monedas = listar_monedas()
    monedas_activas = [moneda for moneda in monedas if moneda["esta_activa"]]

    return {
        "monedas": monedas,
        "monedas_activas": monedas_activas,
        "cantidad_monedas": len(monedas),
        "cantidad_monedas_activas": len(monedas_activas),
    }


def obtener_contexto_monedas_activas() -> dict[str, Any]:
    """
    Devuelve contexto minimo de monedas activas para formularios.

    No carga datos operativos ni cotizaciones.
    """
    monedas = listar_monedas_activas()

    return {
        "monedas": monedas,
        "cantidad_monedas": len(monedas),
    }


def obtener_contexto_detalle_moneda(codigo_moneda: Any) -> dict[str, Any]:
    """Devuelve contexto chico para edicion de una moneda."""
    codigo_moneda_normalizado = normalizar_codigo_moneda_desde_formulario(
        codigo_moneda
    )
    moneda = obtener_moneda_por_codigo(codigo_moneda_normalizado)

    if moneda is None:
        raise ValueError("No existe la moneda informada.")

    return {"moneda": moneda}


def obtener_moneda_activa_por_codigo(codigo_moneda: Any) -> dict[str, Any]:
    """
    Devuelve una moneda activa por codigo.

    El service normaliza entrada funcional minima y delega validacion final al
    repository.
    """
    codigo_moneda_normalizado = normalizar_codigo_moneda_desde_formulario(
        codigo_moneda
    )

    validar_moneda_activa(codigo_moneda_normalizado)

    moneda = obtener_moneda_por_codigo(codigo_moneda_normalizado)

    if moneda is None:
        raise ValueError("No existe la moneda informada.")

    return moneda


def crear_moneda_desde_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """Crea una moneda desde datos de formulario."""
    return crear_moneda(_normalizar_datos_moneda_formulario(formulario))


def actualizar_moneda_desde_formulario(
    codigo_moneda: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza una moneda desde datos de formulario."""
    return actualizar_moneda_por_codigo(
        codigo_moneda,
        _normalizar_datos_moneda_formulario(formulario),
    )


def activar_moneda(codigo_moneda: Any) -> dict[str, Any]:
    """Activa una moneda sin borrado fisico."""
    return cambiar_estado_moneda(codigo_moneda, 1)


def desactivar_moneda(codigo_moneda: Any) -> dict[str, Any]:
    """Desactiva una moneda sin borrado fisico."""
    return cambiar_estado_moneda(codigo_moneda, 0)


def normalizar_codigo_moneda_desde_formulario(codigo_moneda: Any) -> str:
    """Normaliza codigo de moneda recibido desde formularios."""
    codigo_moneda_normalizado = str(codigo_moneda or "").strip().upper()

    if not codigo_moneda_normalizado:
        raise ValueError("El codigo de moneda es obligatorio.")

    return codigo_moneda_normalizado


def _normalizar_datos_moneda_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de monedas."""
    return {
        "codigo": _obtener_valor_formulario(formulario, "codigo"),
        "nombre": _obtener_valor_formulario(formulario, "nombre"),
        "simbolo": _obtener_valor_formulario(formulario, "simbolo"),
        "decimales": _obtener_valor_formulario(formulario, "decimales"),
        "activa": _obtener_valor_checkbox_0_1(formulario, "activa"),
        "orden": _obtener_valor_formulario(formulario, "orden"),
    }


def _obtener_valor_formulario(formulario: dict[str, Any], campo: str) -> str:
    """Lee valor de formulario y devuelve texto recortado."""
    return str(formulario.get(campo, "") or "").strip()


def _obtener_valor_checkbox_0_1(formulario: dict[str, Any], campo: str) -> int:
    """Normaliza checkbox HTML al contrato SQLite 0/1."""
    valor = formulario.get(campo)

    if valor is None:
        return 0

    valor_normalizado = str(valor or "").strip().upper()

    if valor_normalizado in {"", "0", "NO", "FALSE", "OFF"}:
        return 0

    return 1
