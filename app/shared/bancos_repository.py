import sqlite3
from datetime import datetime
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


def crear_banco(datos_banco: dict[str, Any]) -> dict[str, Any]:
    """Inserta un banco manual y devuelve la fila creada."""
    codigo = _validar_codigo(datos_banco["codigo"])
    nombre = _validar_nombre(datos_banco["nombre"])
    activo = _validar_activo(datos_banco.get("activo", 1))
    orden = _validar_orden(datos_banco.get("orden", 0))
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            db.execute(
                """
                INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (codigo, nombre, activo, orden, creado_en),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo crear el banco. Revise el codigo informado.") from exc

    banco = obtener_banco_por_codigo(codigo)

    if banco is None:
        raise ValueError("No se pudo recuperar el banco creado.")

    return banco


def actualizar_banco_por_codigo(
    codigo: Any,
    datos_banco: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de un banco y devuelve la fila final."""
    codigo_validado = _validar_codigo(codigo)

    if obtener_banco_por_codigo(codigo_validado) is None:
        raise ValueError("No existe el banco informado.")

    nombre = _validar_nombre(datos_banco["nombre"])
    activo = _validar_activo(datos_banco.get("activo", 1))
    orden = _validar_orden(datos_banco.get("orden", 0))
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE bancos
            SET nombre = ?, activo = ?, orden = ?, actualizado_en = ?
            WHERE codigo = ?
            """,
            (nombre, activo, orden, actualizado_en, codigo_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el banco.")

    banco = obtener_banco_por_codigo(codigo_validado)

    if banco is None:
        raise ValueError("No se pudo recuperar el banco actualizado.")

    return banco


def cambiar_estado_banco(codigo: Any, activo: Any) -> dict[str, Any]:
    """Activa o desactiva un banco sin borrarlo fisicamente."""
    codigo_validado = _validar_codigo(codigo)
    activo_validado = _validar_activo(activo)

    if obtener_banco_por_codigo(codigo_validado) is None:
        raise ValueError("No existe el banco informado.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE bancos
            SET activo = ?, actualizado_en = ?
            WHERE codigo = ?
            """,
            (activo_validado, actualizado_en, codigo_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el estado del banco.")

    banco = obtener_banco_por_codigo(codigo_validado)

    if banco is None:
        raise ValueError("No se pudo recuperar el banco actualizado.")

    return banco


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


def _validar_nombre(nombre: Any) -> str:
    nombre_validado = str(nombre or "").strip().upper()

    if not nombre_validado:
        raise ValueError("El nombre del banco es obligatorio.")

    return nombre_validado


def _validar_activo(activo: Any) -> int:
    if isinstance(activo, bool):
        return 1 if activo else 0

    if isinstance(activo, int) and activo in (0, 1):
        return activo

    activo_normalizado = str(activo or "").strip()

    if activo_normalizado in {"0", "1"}:
        return int(activo_normalizado)

    raise ValueError("El estado activo del banco es invalido.")


def _validar_orden(orden: Any) -> int:
    try:
        orden_validado = int(str(orden or "0").strip())
    except ValueError as exc:
        raise ValueError("El orden del banco debe ser numerico.") from exc

    if orden_validado < 0:
        raise ValueError("El orden del banco no puede ser negativo.")

    return orden_validado
