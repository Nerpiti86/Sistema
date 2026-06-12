from typing import Any

from app.shared.bancos_repository import (
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


def normalizar_codigo_banco_desde_formulario(codigo_banco: Any) -> str:
    """Normaliza codigo de banco recibido desde formularios."""
    codigo_banco_normalizado = str(codigo_banco or "").strip().upper()

    if not codigo_banco_normalizado:
        raise ValueError("El codigo de banco es obligatorio.")

    return codigo_banco_normalizado
