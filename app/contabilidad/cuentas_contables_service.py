from typing import Any

from app.contabilidad.cuentas_contables_repository import (
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
