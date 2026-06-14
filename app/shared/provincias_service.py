from typing import Any

from app.shared.paises_repository import (
    listar_paises_activos,
    validar_pais_activo,
)
from app.shared.provincias_repository import (
    actualizar_provincia_por_id,
    cambiar_estado_provincia,
    crear_provincia,
    listar_provincias,
    listar_provincias_activas_por_pais,
    listar_provincias_por_pais,
    obtener_provincia_por_id,
    validar_provincia_activa,
)


def obtener_contexto_listado_provincias() -> dict[str, Any]:
    """
    Devuelve contexto chico del maestro provincias.

    Este service delega lecturas y escrituras en repositories compartidos.
    """
    provincias = listar_provincias()
    provincias_activas = [provincia for provincia in provincias if provincia["esta_activa"]]

    return {
        "provincias": provincias,
        "provincias_activas": provincias_activas,
        "cantidad_provincias": len(provincias),
        "cantidad_provincias_activas": len(provincias_activas),
    }


def obtener_contexto_provincias_por_pais(pais_id: Any) -> dict[str, Any]:
    """Devuelve contexto de provincias de un pais activo."""
    pais_id_normalizado = normalizar_id_pais_desde_formulario(pais_id)
    validar_pais_activo(pais_id_normalizado)
    provincias = listar_provincias_por_pais(pais_id_normalizado)

    return {
        "pais_id": pais_id_normalizado,
        "provincias": provincias,
        "cantidad_provincias": len(provincias),
    }


def obtener_contexto_provincias_activas_por_pais(pais_id: Any) -> dict[str, Any]:
    """Devuelve contexto minimo de provincias activas de un pais activo."""
    pais_id_normalizado = normalizar_id_pais_desde_formulario(pais_id)
    validar_pais_activo(pais_id_normalizado)
    provincias = listar_provincias_activas_por_pais(pais_id_normalizado)

    return {
        "pais_id": pais_id_normalizado,
        "provincias": provincias,
        "cantidad_provincias": len(provincias),
    }


def obtener_contexto_formulario_provincia(
    provincia: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Devuelve contexto para formularios de provincias con paises activos."""
    paises = listar_paises_activos()
    provincia_form = dict(provincia or {})
    provincia_form.setdefault("activo", 1)
    provincia_form.setdefault("orden", 0)

    return {
        "provincia": provincia_form,
        "paises": paises,
        "cantidad_paises": len(paises),
    }


def obtener_contexto_detalle_provincia(
    provincia_id: Any,
) -> dict[str, Any]:
    """Devuelve contexto chico para edicion de una provincia."""
    provincia_id_normalizado = normalizar_id_provincia_desde_formulario(provincia_id)
    provincia = obtener_provincia_por_id(provincia_id_normalizado)

    if provincia is None:
        raise ValueError("No existe la provincia informada.")

    return {"provincia": provincia}


def obtener_provincia_activa_por_id(provincia_id: Any) -> dict[str, Any]:
    """
    Devuelve una provincia activa por id.

    El service normaliza entrada funcional minima y delega validacion final al
    repository.
    """
    provincia_id_normalizado = normalizar_id_provincia_desde_formulario(provincia_id)

    validar_provincia_activa(provincia_id_normalizado)

    provincia = obtener_provincia_por_id(provincia_id_normalizado)

    if provincia is None:
        raise ValueError("No existe la provincia informada.")

    return provincia


def crear_provincia_desde_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Crea una provincia desde datos de formulario."""
    datos_provincia = _normalizar_datos_provincia_formulario(formulario)
    validar_pais_activo(datos_provincia["pais_id"])

    return crear_provincia(datos_provincia)


def actualizar_provincia_desde_formulario(
    provincia_id: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza una provincia desde datos de formulario."""
    datos_provincia = _normalizar_datos_provincia_formulario(formulario)
    validar_pais_activo(datos_provincia["pais_id"])

    return actualizar_provincia_por_id(
        provincia_id,
        datos_provincia,
    )


def activar_provincia(provincia_id: Any) -> dict[str, Any]:
    """Activa una provincia sin borrado fisico."""
    return cambiar_estado_provincia(provincia_id, 1)


def desactivar_provincia(provincia_id: Any) -> dict[str, Any]:
    """Desactiva una provincia sin borrado fisico."""
    return cambiar_estado_provincia(provincia_id, 0)


def normalizar_id_provincia_desde_formulario(provincia_id: Any) -> int:
    """Normaliza id de provincia recibido desde formularios."""
    try:
        provincia_id_normalizado = int(str(provincia_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id de la provincia debe ser numerico.") from exc

    if provincia_id_normalizado <= 0:
        raise ValueError("El id de la provincia debe ser positivo.")

    return provincia_id_normalizado


def normalizar_id_pais_desde_formulario(pais_id: Any) -> int:
    """Normaliza id de pais recibido desde formularios."""
    try:
        pais_id_normalizado = int(str(pais_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del pais debe ser numerico.") from exc

    if pais_id_normalizado <= 0:
        raise ValueError("El id del pais debe ser positivo.")

    return pais_id_normalizado


def _normalizar_datos_provincia_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de provincias."""
    return {
        "pais_id": normalizar_id_pais_desde_formulario(
            _obtener_valor_formulario(formulario, "pais_id")
        ),
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
