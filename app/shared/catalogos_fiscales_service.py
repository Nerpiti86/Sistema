from typing import Any

from app.shared.catalogos_fiscales_repository import (
    actualizar_item_catalogo_fiscal_por_codigo,
    cambiar_estado_item_catalogo_fiscal,
    crear_item_catalogo_fiscal,
    listar_catalogo_fiscal,
    listar_catalogo_fiscal_activo,
    obtener_item_catalogo_fiscal_por_codigo,
    validar_item_catalogo_fiscal_activo,
)


def obtener_contexto_listado_catalogo_fiscal(catalogo: str, nombre_plural: str) -> dict[str, Any]:
    """Devuelve contexto chico de listado para un catalogo fiscal."""
    items = listar_catalogo_fiscal(catalogo)
    items_activos = [item for item in items if item["esta_activo"]]

    return {
        nombre_plural: items,
        f"{nombre_plural}_activos": items_activos,
        f"cantidad_{nombre_plural}": len(items),
        f"cantidad_{nombre_plural}_activos": len(items_activos),
    }


def obtener_contexto_catalogo_fiscal_activo(catalogo: str, nombre_plural: str) -> dict[str, Any]:
    """Devuelve items activos de un catalogo fiscal para formularios."""
    items = listar_catalogo_fiscal_activo(catalogo)

    return {
        nombre_plural: items,
        f"cantidad_{nombre_plural}": len(items),
    }


def obtener_contexto_detalle_catalogo_fiscal(
    catalogo: str,
    codigo: Any,
    nombre_singular: str,
) -> dict[str, Any]:
    """Devuelve contexto chico de detalle para un item de catalogo fiscal."""
    codigo_normalizado = normalizar_codigo_catalogo_fiscal_desde_formulario(codigo, nombre_singular)
    item = obtener_item_catalogo_fiscal_por_codigo(catalogo, codigo_normalizado)

    if item is None:
        raise ValueError(f"No existe {nombre_singular} informado.")

    return {nombre_singular: item}


def obtener_item_catalogo_fiscal_activo(
    catalogo: str,
    codigo: Any,
) -> dict[str, Any]:
    """Devuelve un item activo de catalogo fiscal por codigo."""
    validar_item_catalogo_fiscal_activo(catalogo, codigo)
    item = obtener_item_catalogo_fiscal_por_codigo(catalogo, codigo)

    if item is None:
        raise ValueError("No existe el item de catalogo fiscal informado.")

    return item


def crear_item_catalogo_fiscal_desde_formulario(
    catalogo: str,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Crea un item de catalogo fiscal desde formulario."""
    return crear_item_catalogo_fiscal(catalogo, _normalizar_datos_catalogo_formulario(formulario))


def actualizar_item_catalogo_fiscal_desde_formulario(
    catalogo: str,
    codigo: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza un item de catalogo fiscal desde formulario."""
    return actualizar_item_catalogo_fiscal_por_codigo(
        catalogo,
        codigo,
        _normalizar_datos_catalogo_formulario(formulario),
    )


def activar_item_catalogo_fiscal(catalogo: str, codigo: Any) -> dict[str, Any]:
    """Activa un item de catalogo fiscal sin borrado fisico."""
    return cambiar_estado_item_catalogo_fiscal(catalogo, codigo, 1)


def desactivar_item_catalogo_fiscal(catalogo: str, codigo: Any) -> dict[str, Any]:
    """Desactiva un item de catalogo fiscal sin borrado fisico."""
    return cambiar_estado_item_catalogo_fiscal(catalogo, codigo, 0)


def normalizar_codigo_catalogo_fiscal_desde_formulario(codigo: Any, nombre_singular: str) -> str:
    """Normaliza codigo de catalogo fiscal recibido desde formularios."""
    codigo_normalizado = str(codigo or "").strip()

    if not codigo_normalizado:
        raise ValueError(f"El codigo de {nombre_singular} es obligatorio.")

    return codigo_normalizado


def _normalizar_datos_catalogo_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """Normaliza campos comunes recibidos desde formularios fiscales."""
    return {
        "codigo": _obtener_valor_formulario(formulario, "codigo"),
        "descripcion": _obtener_valor_formulario(formulario, "descripcion"),
        "activo": _obtener_valor_checkbox_0_1(formulario, "activo"),
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
