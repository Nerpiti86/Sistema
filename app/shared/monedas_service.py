from typing import Any

from app.shared.monedas_repository import (
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


def normalizar_codigo_moneda_desde_formulario(codigo_moneda: Any) -> str:
    """Normaliza codigo de moneda recibido desde formularios."""
    codigo_moneda_normalizado = str(codigo_moneda or "").strip().upper()

    if not codigo_moneda_normalizado:
        raise ValueError("El codigo de moneda es obligatorio.")

    return codigo_moneda_normalizado
