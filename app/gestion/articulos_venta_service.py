from typing import Any

from app.contabilidad.cuentas_contables_repository import (
    listar_cuentas_contables,
    validar_cuenta_contable_imputable,
)
from app.gestion.articulos_venta_repository import (
    actualizar_articulo_venta_por_id,
    cambiar_estado_articulo_venta,
    crear_articulo_venta,
    listar_articulos_venta,
    obtener_articulo_venta_por_id,
)
from app.shared.monedas_repository import listar_monedas_activas, validar_moneda_activa

_TIPOS_ARTICULO_VENTA = ("PRODUCTO", "SERVICIO")


def obtener_contexto_listado_articulos_venta() -> dict[str, Any]:
    """
    Devuelve contexto chico del maestro productos o servicios.

    Este service no ejecuta SQL directo. La lectura queda delegada al repository
    funcional de gestion.
    """
    articulos_venta = listar_articulos_venta()
    articulos_venta_activos = [
        articulo for articulo in articulos_venta if articulo["esta_activo"]
    ]

    return {
        "articulos_venta": articulos_venta,
        "articulos_venta_activos": articulos_venta_activos,
        "cantidad_articulos_venta": len(articulos_venta),
        "cantidad_articulos_venta_activos": len(articulos_venta_activos),
    }


def obtener_contexto_formulario_articulo_venta(
    articulo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Devuelve contexto para formularios de productos o servicios."""
    articulo_form = dict(articulo or {})
    articulo_form.setdefault("activo", 1)
    articulo_form.setdefault("orden", 0)

    monedas = listar_monedas_activas()
    cuentas_contables_imputables = [
        cuenta
        for cuenta in listar_cuentas_contables()
        if cuenta["es_imputable"]
    ]

    return {
        "articulo": articulo_form,
        "tipos_articulo_venta": list(_TIPOS_ARTICULO_VENTA),
        "monedas": monedas,
        "cuentas_contables_imputables": cuentas_contables_imputables,
        "cantidad_tipos_articulo_venta": len(_TIPOS_ARTICULO_VENTA),
        "cantidad_monedas": len(monedas),
        "cantidad_cuentas_contables_imputables": len(cuentas_contables_imputables),
    }


def obtener_contexto_edicion_articulo_venta(articulo_venta_id: Any) -> dict[str, Any]:
    """Devuelve contexto para editar un producto o servicio existente."""
    articulo_venta_id_normalizado = normalizar_id_articulo_venta_desde_formulario(
        articulo_venta_id
    )
    articulo = obtener_articulo_venta_por_id(articulo_venta_id_normalizado)

    if articulo is None:
        raise ValueError("No existe el producto o servicio informado.")

    return obtener_contexto_formulario_articulo_venta(articulo)


def crear_articulo_venta_desde_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Crea un producto o servicio desde datos de formulario."""
    datos_articulo = _normalizar_datos_articulo_venta_formulario(formulario)
    _validar_referencias_operativas_articulo_venta(datos_articulo)

    return crear_articulo_venta(datos_articulo)


def actualizar_articulo_venta_desde_formulario(
    articulo_venta_id: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza un producto o servicio desde datos de formulario."""
    datos_articulo = _normalizar_datos_articulo_venta_formulario(formulario)
    _validar_referencias_operativas_articulo_venta(datos_articulo)

    return actualizar_articulo_venta_por_id(articulo_venta_id, datos_articulo)


def activar_articulo_venta(articulo_venta_id: Any) -> dict[str, Any]:
    """Activa un producto o servicio sin borrado fisico."""
    return cambiar_estado_articulo_venta(articulo_venta_id, 1)


def desactivar_articulo_venta(articulo_venta_id: Any) -> dict[str, Any]:
    """Desactiva un producto o servicio sin borrado fisico."""
    return cambiar_estado_articulo_venta(articulo_venta_id, 0)


def normalizar_id_articulo_venta_desde_formulario(articulo_venta_id: Any) -> int:
    """Normaliza id de producto o servicio recibido desde formularios."""
    try:
        articulo_venta_id_normalizado = int(str(articulo_venta_id).strip())
    except ValueError as exc:
        raise ValueError("El id del producto o servicio debe ser numerico.") from exc

    if articulo_venta_id_normalizado <= 0:
        raise ValueError("El id del producto o servicio debe ser positivo.")

    return articulo_venta_id_normalizado


def _normalizar_datos_articulo_venta_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de productos o servicios."""
    return {
        "nombre": _obtener_valor_formulario(formulario, "nombre"),
        "tipo": _obtener_valor_formulario(formulario, "tipo"),
        "moneda_codigo": _obtener_valor_formulario(formulario, "moneda_codigo"),
        "precio_unitario_sugerido_1000000": _obtener_valor_formulario(
            formulario,
            "precio_unitario_sugerido_1000000",
        ),
        "cuenta_ingreso_codigo": _obtener_valor_formulario(
            formulario,
            "cuenta_ingreso_codigo",
        ),
        "activo": _obtener_valor_checkbox_0_1(formulario, "activo"),
        "orden": _obtener_valor_formulario(formulario, "orden"),
        "observaciones": _obtener_valor_formulario(formulario, "observaciones"),
    }


def _validar_referencias_operativas_articulo_venta(
    datos_articulo: dict[str, Any],
) -> None:
    """Valida referencias activas antes de delegar persistencia al repository."""
    moneda_codigo = _normalizar_texto_opcional(datos_articulo.get("moneda_codigo"))

    if moneda_codigo is None:
        raise ValueError("La moneda del producto o servicio es obligatoria.")

    validar_moneda_activa(moneda_codigo)

    cuenta_ingreso_codigo = _normalizar_texto_opcional(
        datos_articulo.get("cuenta_ingreso_codigo")
    )

    if cuenta_ingreso_codigo is not None:
        validar_cuenta_contable_imputable(cuenta_ingreso_codigo)


def _normalizar_texto_opcional(valor: Any) -> str | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return valor_normalizado


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
