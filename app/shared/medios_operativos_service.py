from typing import Any

from app.shared.bancos_repository import listar_bancos_activos
from app.shared.medios_operativos_repository import (
    TIPOS_MEDIO_OPERATIVO,
    actualizar_medio_operativo_por_codigo,
    cambiar_estado_medio_operativo,
    crear_medio_operativo,
    listar_medios_operativos,
    listar_medios_operativos_activos,
    obtener_medio_operativo_por_codigo,
    validar_medio_operativo_activo,
)
from app.shared.monedas_repository import listar_monedas_activas
from app.contabilidad.cuentas_contables_repository import (
    obtener_cuenta_contable_por_cuenta,
    validar_cuenta_contable_imputable,
)

_TIPOS_MEDIO_OPERATIVO_LABELS = {
    "BANCO_PROPIO": "Banco propio",
    "EFECTIVO": "Efectivo",
    "TARJETA": "Tarjeta",
    "VALORES_CARTERA": "Valores en cartera",
}


def obtener_contexto_listado_medios_operativos() -> dict[str, Any]:
    """Devuelve contexto del maestro medios operativos."""
    medios = listar_medios_operativos()
    medios_activos = [medio for medio in medios if medio["esta_activo"]]

    return {
        "medios_operativos": medios,
        "medios_operativos_activos": medios_activos,
        "cantidad_medios_operativos": len(medios),
        "cantidad_medios_operativos_activos": len(medios_activos),
        "tipos_medios_operativos": obtener_tipos_medios_operativos(),
    }


def obtener_contexto_formulario_medio_operativo(
    medio_operativo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Devuelve datos auxiliares para alta o edicion de medios operativos."""
    return {
        "medio_operativo": medio_operativo or {
            "activo": 1,
            "requiere_cotizacion": 0,
            "tipo": "EFECTIVO",
            "cotizacion_default_centavos": "",
            "orden": 0,
        },
        "tipos_medios_operativos": obtener_tipos_medios_operativos(),
        "monedas": listar_monedas_activas(),
        "bancos": listar_bancos_activos(),
    }


def obtener_contexto_detalle_medio_operativo(codigo: Any) -> dict[str, Any]:
    """Devuelve contexto chico para edicion de un medio operativo."""
    codigo_normalizado = normalizar_codigo_medio_operativo_desde_formulario(codigo)
    medio_operativo = obtener_medio_operativo_por_codigo(codigo_normalizado)

    if medio_operativo is None:
        raise ValueError("No existe el medio operativo informado.")

    return {"medio_operativo": medio_operativo}


def obtener_medio_operativo_activo_por_codigo(codigo: Any) -> dict[str, Any]:
    """Devuelve un medio operativo activo por codigo visual."""
    codigo_normalizado = normalizar_codigo_medio_operativo_desde_formulario(codigo)
    validar_medio_operativo_activo(codigo_normalizado)
    medio_operativo = obtener_medio_operativo_por_codigo(codigo_normalizado)

    if medio_operativo is None:
        raise ValueError("No existe el medio operativo informado.")

    return medio_operativo


def obtener_contexto_medios_operativos_activos() -> dict[str, Any]:
    """Devuelve medios operativos activos para selects o lookups."""
    medios = listar_medios_operativos_activos()

    return {
        "medios_operativos": medios,
        "cantidad_medios_operativos": len(medios),
    }


def crear_medio_operativo_desde_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Crea un medio operativo desde datos de formulario."""
    datos = _normalizar_datos_medio_operativo_formulario(formulario)
    _validar_cuenta_contable_imputable(datos["cuenta_contable_codigo"])
    return crear_medio_operativo(datos)


def actualizar_medio_operativo_desde_formulario(
    codigo: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza un medio operativo desde datos de formulario."""
    datos = _normalizar_datos_medio_operativo_formulario(formulario)
    _validar_cuenta_contable_imputable(datos["cuenta_contable_codigo"])
    return actualizar_medio_operativo_por_codigo(codigo, datos)


def activar_medio_operativo(codigo: Any) -> dict[str, Any]:
    """Activa un medio operativo sin borrado fisico."""
    return cambiar_estado_medio_operativo(codigo, 1)


def desactivar_medio_operativo(codigo: Any) -> dict[str, Any]:
    """Desactiva un medio operativo sin borrado fisico."""
    return cambiar_estado_medio_operativo(codigo, 0)


def obtener_tipos_medios_operativos() -> list[dict[str, str]]:
    """Devuelve tipos cerrados disponibles para formulario."""
    return [
        {"codigo": codigo, "nombre": _TIPOS_MEDIO_OPERATIVO_LABELS[codigo]}
        for codigo in sorted(TIPOS_MEDIO_OPERATIVO)
    ]


def normalizar_codigo_medio_operativo_desde_formulario(codigo: Any) -> str:
    """Normaliza codigo visible de medio operativo recibido desde formularios."""
    codigo_normalizado = str(codigo or "").strip().upper()

    if not codigo_normalizado:
        raise ValueError("El codigo del medio operativo es obligatorio.")

    return codigo_normalizado


def _normalizar_datos_medio_operativo_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de medios operativos."""
    return {
        "codigo": _obtener_valor_formulario(formulario, "codigo"),
        "nombre": _obtener_valor_formulario(formulario, "nombre"),
        "tipo": _obtener_valor_formulario(formulario, "tipo"),
        "requiere_cotizacion": _obtener_valor_checkbox_0_1(
            formulario,
            "requiere_cotizacion",
        ),
        "cotizacion_default_centavos": _obtener_valor_formulario(
            formulario,
            "cotizacion_default_centavos",
        ),
        "banco_codigo": _obtener_valor_formulario(formulario, "banco_codigo"),
        "plaza": _obtener_valor_formulario(formulario, "plaza"),
        "sucursal": _obtener_valor_formulario(formulario, "sucursal"),
        "numero_cuenta": _obtener_valor_formulario(formulario, "numero_cuenta"),
        "cuenta_contable_codigo": _obtener_valor_formulario(
            formulario,
            "cuenta_contable_codigo",
        ),
        "moneda_codigo": _obtener_valor_formulario(formulario, "moneda_codigo"),
        "cuit": _obtener_valor_formulario(formulario, "cuit"),
        "activo": _obtener_valor_checkbox_0_1(formulario, "activo"),
        "orden": _obtener_valor_formulario(formulario, "orden"),
    }


def _validar_cuenta_contable_imputable(cuenta_contable_codigo: str) -> None:
    try:
        validar_cuenta_contable_imputable(cuenta_contable_codigo)
    except ValueError as exc:
        cuenta_contable = obtener_cuenta_contable_por_cuenta(cuenta_contable_codigo)
        if cuenta_contable is None:
            raise ValueError("La cuenta contable del medio operativo no existe.") from exc
        raise ValueError("La cuenta contable del medio operativo debe ser imputable.") from exc


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
