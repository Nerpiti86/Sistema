from typing import Any

from app.contabilidad.cuentas_contables_repository import (
    actualizar_cuenta_contable_por_cuenta,
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


def obtener_disponibilidad_cuenta_contable(
    cuenta_contable_codigo: str,
) -> dict[str, Any]:
    """
    Devuelve disponibilidad funcional de una cuenta contable.

    Este service no ejecuta SQL directo. Normaliza entrada minima y consulta al
    repository para informar si el codigo ya esta ocupado antes del submit.
    """
    cuenta_contable_codigo_normalizado = str(cuenta_contable_codigo or "").strip()

    if not cuenta_contable_codigo_normalizado:
        raise ValueError("La cuenta contable es obligatoria.")

    try:
        cuenta_contable = obtener_cuenta_contable_por_cuenta(
            cuenta_contable_codigo_normalizado
        )
    except ValueError as exc:
        raise ValueError(
            "La cuenta contable debe respetar el formato 9.9.99.99.999."
        ) from exc

    if cuenta_contable is None:
        return {
            "cuenta": cuenta_contable_codigo_normalizado,
            "disponible": True,
            "ocupada": False,
            "descripcion": "",
            "mensaje": "Cuenta contable disponible.",
        }

    return {
        "cuenta": cuenta_contable["cuenta"],
        "disponible": False,
        "ocupada": True,
        "descripcion": cuenta_contable["descripcion"],
        "mensaje": "La cuenta contable ya esta ocupada.",
    }


def crear_cuenta_contable_desde_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """
    Crea una cuenta contable desde datos de formulario.

    El service no ejecuta SQL directo. Normaliza la entrada de pantalla y
    delega la persistencia al repository de cuentas_contables.
    """
    datos_cuenta_contable = _normalizar_datos_cuenta_contable_formulario(formulario)

    return crear_cuenta_contable(datos_cuenta_contable)


def _obtener_valor_formulario(formulario: dict[str, Any], campo: str) -> str:
    """Lee valor de formulario y devuelve texto recortado."""
    return str(formulario.get(campo, "") or "").strip()


def _obtener_valor_checkbox_0_1(formulario: dict[str, Any], campo: str) -> int:
    """
    Normaliza checkbox HTML al contrato SQLite 0/1.

    Si el navegador no envia el campo, el checkbox esta destildado.
    """
    valor = formulario.get(campo)

    if valor is None:
        return 0

    valor_normalizado = str(valor or "").strip().upper()

    if valor_normalizado in {"", "0", "NO", "FALSE", "OFF"}:
        return 0

    return 1


def actualizar_cuenta_contable_desde_formulario(
    cuenta_contable_codigo: str,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """
    Actualiza una cuenta contable desde datos de formulario.

    El service no ejecuta SQL directo. Normaliza la entrada de pantalla y
    delega la persistencia al repository de cuentas_contables.
    """
    datos_cuenta_contable = _normalizar_datos_cuenta_contable_formulario(formulario)

    return actualizar_cuenta_contable_por_cuenta(
        cuenta_contable_codigo,
        datos_cuenta_contable,
    )


def _normalizar_datos_cuenta_contable_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza campos de formulario de cuentas_contables."""
    return {
        "cuenta": _obtener_valor_formulario(formulario, "cuenta"),
        "descripcion": _obtener_valor_formulario(formulario, "descripcion"),
        "saldo_habitual": _obtener_valor_formulario(formulario, "saldo_habitual"),
        "naturaleza": _obtener_valor_formulario(formulario, "naturaleza"),
        "imputable": _obtener_valor_checkbox_0_1(formulario, "imputable"),
        "monetaria": _obtener_valor_checkbox_0_1(formulario, "monetaria"),
        "sumarizadora": _obtener_valor_formulario(formulario, "sumarizadora"),
    }
