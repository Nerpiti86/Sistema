from typing import Any

from app.gestion.grupos_clientes_repository import (
    actualizar_grupo_cliente_por_id,
    cambiar_estado_grupo_cliente,
    crear_grupo_cliente,
    listar_grupos_clientes,
    listar_grupos_clientes_activos,
    obtener_grupo_cliente_por_id,
    validar_grupo_cliente_activo,
)


def obtener_contexto_listado_grupos_clientes() -> dict[str, Any]:
    """
    Devuelve contexto chico del maestro grupos de clientes.

    Este service no ejecuta SQL directo. La lectura queda delegada al repository
    funcional de gestion.
    """
    grupos = listar_grupos_clientes()
    grupos_activos = [grupo for grupo in grupos if grupo["esta_activo"]]

    return {
        "grupos_clientes": grupos,
        "grupos_clientes_activos": grupos_activos,
        "cantidad_grupos_clientes": len(grupos),
        "cantidad_grupos_clientes_activos": len(grupos_activos),
    }


def obtener_contexto_grupos_clientes_activos() -> dict[str, Any]:
    """Devuelve contexto minimo de grupos activos para formularios de clientes."""
    grupos = listar_grupos_clientes_activos()

    return {
        "grupos_clientes": grupos,
        "cantidad_grupos_clientes": len(grupos),
    }


def obtener_contexto_detalle_grupo_cliente(
    grupo_cliente_id: Any,
) -> dict[str, Any]:
    """Devuelve contexto chico para edicion de un grupo de clientes."""
    grupo_cliente_id_normalizado = normalizar_id_grupo_cliente_desde_formulario(
        grupo_cliente_id
    )
    grupo = obtener_grupo_cliente_por_id(grupo_cliente_id_normalizado)

    if grupo is None:
        raise ValueError("No existe el grupo de clientes informado.")

    return {"grupo_cliente": grupo}


def obtener_grupo_cliente_activo_por_id(grupo_cliente_id: Any) -> dict[str, Any]:
    """
    Devuelve un grupo de clientes activo por id.

    El service normaliza entrada funcional minima y delega validacion final al
    repository.
    """
    grupo_cliente_id_normalizado = normalizar_id_grupo_cliente_desde_formulario(
        grupo_cliente_id
    )

    validar_grupo_cliente_activo(grupo_cliente_id_normalizado)

    grupo = obtener_grupo_cliente_por_id(grupo_cliente_id_normalizado)

    if grupo is None:
        raise ValueError("No existe el grupo de clientes informado.")

    return grupo


def crear_grupo_cliente_desde_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Crea un grupo de clientes desde datos de formulario."""
    return crear_grupo_cliente(_normalizar_datos_grupo_cliente_formulario(formulario))


def actualizar_grupo_cliente_desde_formulario(
    grupo_cliente_id: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza un grupo de clientes desde datos de formulario."""
    return actualizar_grupo_cliente_por_id(
        grupo_cliente_id,
        _normalizar_datos_grupo_cliente_formulario(formulario),
    )


def activar_grupo_cliente(grupo_cliente_id: Any) -> dict[str, Any]:
    """Activa un grupo de clientes sin borrado fisico."""
    return cambiar_estado_grupo_cliente(grupo_cliente_id, 1)


def desactivar_grupo_cliente(grupo_cliente_id: Any) -> dict[str, Any]:
    """Desactiva un grupo de clientes sin borrado fisico."""
    return cambiar_estado_grupo_cliente(grupo_cliente_id, 0)


def normalizar_id_grupo_cliente_desde_formulario(grupo_cliente_id: Any) -> int:
    """Normaliza id de grupo de clientes recibido desde formularios."""
    try:
        grupo_cliente_id_normalizado = int(str(grupo_cliente_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del grupo de clientes debe ser numerico.") from exc

    if grupo_cliente_id_normalizado <= 0:
        raise ValueError("El id del grupo de clientes debe ser positivo.")

    return grupo_cliente_id_normalizado


def _normalizar_datos_grupo_cliente_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de grupos de clientes."""
    return {
        "nombre": _obtener_valor_formulario(formulario, "nombre"),
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
