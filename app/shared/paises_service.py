from typing import Any

from app.shared.paises_repository import (
    actualizar_pais_por_id,
    cambiar_estado_pais,
    crear_pais,
    listar_paises,
    listar_paises_activos,
    obtener_pais_por_id,
    validar_pais_activo,
)


def obtener_contexto_listado_paises() -> dict[str, Any]:
    """
    Devuelve contexto chico del maestro paises.

    Este service no ejecuta SQL directo. La lectura queda delegada al repository
    funcional de gestion.
    """
    paises = listar_paises()
    paises_activos = [pais for pais in paises if pais["esta_activo"]]

    return {
        "paises": paises,
        "paises_activos": paises_activos,
        "cantidad_paises": len(paises),
        "cantidad_paises_activos": len(paises_activos),
    }


def obtener_contexto_paises_activos() -> dict[str, Any]:
    """Devuelve contexto minimo de paises activos para formularios de gestion."""
    paises = listar_paises_activos()

    return {
        "paises": paises,
        "cantidad_paises": len(paises),
    }


def obtener_contexto_detalle_pais(
    pais_id: Any,
) -> dict[str, Any]:
    """Devuelve contexto chico para edicion de un pais."""
    pais_id_normalizado = normalizar_id_pais_desde_formulario(pais_id)
    pais = obtener_pais_por_id(pais_id_normalizado)

    if pais is None:
        raise ValueError("No existe el pais informado.")

    return {"pais": pais}


def obtener_pais_activo_por_id(pais_id: Any) -> dict[str, Any]:
    """
    Devuelve un pais activo por id.

    El service normaliza entrada funcional minima y delega validacion final al
    repository.
    """
    pais_id_normalizado = normalizar_id_pais_desde_formulario(pais_id)

    validar_pais_activo(pais_id_normalizado)

    pais = obtener_pais_por_id(pais_id_normalizado)

    if pais is None:
        raise ValueError("No existe el pais informado.")

    return pais


def crear_pais_desde_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Crea un pais desde datos de formulario."""
    return crear_pais(_normalizar_datos_pais_formulario(formulario))


def actualizar_pais_desde_formulario(
    pais_id: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza un pais desde datos de formulario."""
    return actualizar_pais_por_id(
        pais_id,
        _normalizar_datos_pais_formulario(formulario),
    )


def activar_pais(pais_id: Any) -> dict[str, Any]:
    """Activa un pais sin borrado fisico."""
    return cambiar_estado_pais(pais_id, 1)


def desactivar_pais(pais_id: Any) -> dict[str, Any]:
    """Desactiva un pais sin borrado fisico."""
    return cambiar_estado_pais(pais_id, 0)


def normalizar_id_pais_desde_formulario(pais_id: Any) -> int:
    """Normaliza id de pais recibido desde formularios."""
    try:
        pais_id_normalizado = int(str(pais_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del pais debe ser numerico.") from exc

    if pais_id_normalizado <= 0:
        raise ValueError("El id del pais debe ser positivo.")

    return pais_id_normalizado


def _normalizar_datos_pais_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de paises."""
    return {
        "nombre": _obtener_valor_formulario(formulario, "nombre"),
        "codigo_iso": _obtener_valor_formulario(formulario, "codigo_iso"),
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
