from typing import Any

from app.db import get_db


def listar_bancos() -> list[dict[str, Any]]:
    """Devuelve bancos ordenados para uso transversal."""
    filas = get_db().execute(
        """
        SELECT id, codigo, nombre, activo, orden, creado_en, actualizado_en
        FROM bancos
        ORDER BY orden, CAST(codigo AS INTEGER)
        """
    ).fetchall()

    return [_normalizar_fila(fila) for fila in filas]


def listar_bancos_activos() -> list[dict[str, Any]]:
    """Devuelve bancos activos ordenados para formularios."""
    filas = get_db().execute(
        """
        SELECT id, codigo, nombre, activo, orden, creado_en, actualizado_en
        FROM bancos
        WHERE activo = 1
        ORDER BY orden, CAST(codigo AS INTEGER)
        """
    ).fetchall()

    return [_normalizar_fila(fila) for fila in filas]


def obtener_banco_por_codigo(codigo: Any) -> dict[str, Any] | None:
    """Devuelve un banco por codigo, o None si no existe."""
    codigo_validado = _validar_codigo(codigo)
    fila = get_db().execute(
        """
        SELECT id, codigo, nombre, activo, orden, creado_en, actualizado_en
        FROM bancos
        WHERE codigo = ?
        LIMIT 1
        """,
        (codigo_validado,),
    ).fetchone()

    if fila is None:
        return None

    return _normalizar_fila(fila)


def validar_banco_activo(codigo: Any) -> bool:
    """Valida que un banco exista y este activo."""
    codigo_validado = _validar_codigo(codigo)
    fila = get_db().execute(
        """
        SELECT 1
        FROM bancos
        WHERE codigo = ? AND activo = 1
        LIMIT 1
        """,
        (codigo_validado,),
    ).fetchone()

    if fila is None:
        raise ValueError("El banco no existe o no esta activo.")

    return True


def _normalizar_fila(fila) -> dict[str, Any]:
    banco = dict(fila)
    banco["activo"] = int(banco["activo"])
    banco["orden"] = int(banco["orden"])
    banco["esta_activo"] = banco["activo"] == 1
    banco["descripcion_select"] = f"{banco['codigo']} - {banco['nombre']}"
    return banco


def _validar_codigo(codigo: Any) -> str:
    codigo_validado = str(codigo or "").strip()

    if not codigo_validado:
        raise ValueError("El codigo de banco es obligatorio.")

    if len(codigo_validado) > 5 or not codigo_validado.isdigit():
        raise ValueError("El codigo de banco debe ser numerico de hasta 5 digitos.")

    return codigo_validado
