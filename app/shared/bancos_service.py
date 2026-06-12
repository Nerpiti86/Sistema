from typing import Any

from app.shared.bancos_repository import (
    actualizar_banco_por_codigo,
    cambiar_estado_banco,
    crear_banco,
    listar_bancos,
    listar_bancos_activos,
    obtener_banco_por_codigo,
    validar_banco_activo,
)


def obtener_contexto_listado_bancos() -> dict[str, Any]:
    """
    Devuelve contexto chico del maestro bancos.

    Este service no ejecuta SQL directo. La lectura queda delegada al
    repository transversal de bancos.
    """
    bancos = listar_bancos()
    bancos_activos = [banco for banco in bancos if banco["esta_activo"]]

    return {
        "bancos": bancos,
        "bancos_activos": bancos_activos,
        "cantidad_bancos": len(bancos),
        "cantidad_bancos_activos": len(bancos_activos),
    }


def obtener_contexto_bancos_activos() -> dict[str, Any]:
    """
    Devuelve contexto minimo de bancos activos para formularios.

    No carga datos operativos de cuentas bancarias ni movimientos.
    """
    bancos = listar_bancos_activos()

    return {
        "bancos": bancos,
        "cantidad_bancos": len(bancos),
    }


def obtener_contexto_detalle_banco(codigo_banco: Any) -> dict[str, Any]:
    """Devuelve contexto chico para edicion de un banco."""
    codigo_banco_normalizado = normalizar_codigo_banco_desde_formulario(codigo_banco)
    banco = obtener_banco_por_codigo(codigo_banco_normalizado)

    if banco is None:
        raise ValueError("No existe el banco informado.")

    return {"banco": banco}


def obtener_banco_activo_por_codigo(codigo_banco: Any) -> dict[str, Any]:
    """
    Devuelve un banco activo por codigo BCRA.

    El service normaliza entrada funcional minima y delega validacion final al
    repository.
    """
    codigo_banco_normalizado = normalizar_codigo_banco_desde_formulario(
        codigo_banco
    )

    validar_banco_activo(codigo_banco_normalizado)

    banco = obtener_banco_por_codigo(codigo_banco_normalizado)

    if banco is None:
        raise ValueError("No existe el banco informado.")

    return banco


def crear_banco_desde_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """Crea un banco desde datos de formulario."""
    return crear_banco(_normalizar_datos_banco_formulario(formulario))


def actualizar_banco_desde_formulario(
    codigo_banco: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza un banco desde datos de formulario."""
    return actualizar_banco_por_codigo(
        codigo_banco,
        _normalizar_datos_banco_formulario(formulario),
    )


def activar_banco(codigo_banco: Any) -> dict[str, Any]:
    """Activa un banco sin borrado fisico."""
    return cambiar_estado_banco(codigo_banco, 1)


def desactivar_banco(codigo_banco: Any) -> dict[str, Any]:
    """Desactiva un banco sin borrado fisico."""
    return cambiar_estado_banco(codigo_banco, 0)


def normalizar_codigo_banco_desde_formulario(codigo_banco: Any) -> str:
    """Normaliza codigo de banco recibido desde formularios."""
    codigo_banco_normalizado = str(codigo_banco or "").strip()

    if not codigo_banco_normalizado:
        raise ValueError("El codigo de banco es obligatorio.")

    return codigo_banco_normalizado


def _normalizar_datos_banco_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de bancos."""
    return {
        "codigo": _obtener_valor_formulario(formulario, "codigo"),
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
