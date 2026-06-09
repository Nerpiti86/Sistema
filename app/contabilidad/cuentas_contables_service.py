from typing import Any

from app.contabilidad.cuentas_contables_repository import (
    crear_cuenta_contable,
    listar_cuentas_contables,
    obtener_cuenta_contable_por_cuenta,
)


def obtener_contexto_listado_cuentas_contables() -> dict[str, Any]:
    """
    Devuelve contexto chico para pantalla de cuentas_contables.

    Este service no ejecuta SQL directo. La lectura queda delegada al
    repository identificable de cuentas_contables.
    """
    cuentas_contables = listar_cuentas_contables()

    return {
        "cuentas_contables": cuentas_contables,
        "cantidad_cuentas_contables": len(cuentas_contables),
    }


def obtener_contexto_detalle_cuenta_contable(
    cuenta_contable_codigo: str,
) -> dict[str, Any]:
    """
    Devuelve contexto chico para detalle de una cuenta contable.

    Este service no ejecuta SQL directo. Valida entrada funcional minima y
    delega la busqueda puntual al repository.
    """
    cuenta_contable_codigo_normalizado = str(cuenta_contable_codigo or "").strip()

    if not cuenta_contable_codigo_normalizado:
        raise ValueError("La cuenta contable es obligatoria.")

    cuenta_contable = obtener_cuenta_contable_por_cuenta(
        cuenta_contable_codigo_normalizado
    )

    if cuenta_contable is None:
        raise ValueError("No existe la cuenta contable informada.")

    return {
        "cuenta_contable": cuenta_contable,
    }


def crear_cuenta_contable_desde_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """
    Crea una cuenta contable desde datos de formulario.

    El service no ejecuta SQL directo. Normaliza la entrada de pantalla y
    delega la persistencia al repository de cuentas_contables.
    """
    datos_cuenta_contable = {
        "cuenta": _obtener_valor_formulario(formulario, "cuenta"),
        "descripcion": _obtener_valor_formulario(formulario, "descripcion"),
        "saldo_habitual": _obtener_valor_formulario(formulario, "saldo_habitual"),
        "naturaleza": _obtener_valor_formulario(formulario, "naturaleza"),
        "imputable": _obtener_valor_formulario(formulario, "imputable"),
        "monetaria": _obtener_valor_formulario(formulario, "monetaria"),
        "sumarizadora": _obtener_valor_formulario(formulario, "sumarizadora"),
    }

    return crear_cuenta_contable(datos_cuenta_contable)


def _obtener_valor_formulario(formulario: dict[str, Any], campo: str) -> str:
    """Lee valor de formulario y devuelve texto recortado."""
    return str(formulario.get(campo, "") or "").strip()
