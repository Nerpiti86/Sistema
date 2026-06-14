import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_GRUPOS_CLIENTES = """
    id,
    nombre,
    activo,
    orden,
    creado_en,
    actualizado_en
"""


def listar_grupos_clientes() -> list[dict[str, Any]]:
    """
    Devuelve grupos de clientes ordenados para gestion.

    El maestro no se pagina en esta etapa porque se espera un catalogo chico de
    segmentacion comercial.
    """
    filas_grupos = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_GRUPOS_CLIENTES}
        FROM grupos_clientes
        ORDER BY activo DESC, orden, nombre
        """
    ).fetchall()

    return [_normalizar_fila_grupo_cliente(fila_grupo) for fila_grupo in filas_grupos]


def listar_grupos_clientes_activos() -> list[dict[str, Any]]:
    """Devuelve grupos activos ordenados para selects de clientes."""
    filas_grupos = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_GRUPOS_CLIENTES}
        FROM grupos_clientes
        WHERE activo = 1
        ORDER BY orden, nombre
        """
    ).fetchall()

    return [_normalizar_fila_grupo_cliente(fila_grupo) for fila_grupo in filas_grupos]


def obtener_grupo_cliente_por_id(grupo_cliente_id: Any) -> dict[str, Any] | None:
    """Devuelve un grupo de clientes por id, o None si no existe."""
    grupo_cliente_id_validado = _validar_id_grupo_cliente(grupo_cliente_id)

    fila_grupo = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_GRUPOS_CLIENTES}
        FROM grupos_clientes
        WHERE id = ?
        LIMIT 1
        """,
        (grupo_cliente_id_validado,),
    ).fetchone()

    if fila_grupo is None:
        return None

    return _normalizar_fila_grupo_cliente(fila_grupo)


def crear_grupo_cliente(datos_grupo_cliente: dict[str, Any]) -> dict[str, Any]:
    """Inserta un grupo de clientes y devuelve la fila creada."""
    nombre = _validar_nombre_grupo_cliente(datos_grupo_cliente["nombre"])
    activo = _validar_activo(datos_grupo_cliente.get("activo", 1))
    orden = _validar_orden(datos_grupo_cliente.get("orden", 0))
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                INSERT INTO grupos_clientes (
                    nombre,
                    activo,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (nombre, activo, orden, creado_en),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear el grupo de clientes. Revise el nombre informado."
        ) from exc

    grupo = obtener_grupo_cliente_por_id(cursor.lastrowid)

    if grupo is None:
        raise ValueError("No se pudo recuperar el grupo de clientes creado.")

    return grupo


def actualizar_grupo_cliente_por_id(
    grupo_cliente_id: Any,
    datos_grupo_cliente: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de un grupo de clientes y devuelve la fila final."""
    grupo_cliente_id_validado = _validar_id_grupo_cliente(grupo_cliente_id)

    if obtener_grupo_cliente_por_id(grupo_cliente_id_validado) is None:
        raise ValueError("No existe el grupo de clientes informado.")

    nombre = _validar_nombre_grupo_cliente(datos_grupo_cliente["nombre"])
    activo = _validar_activo(datos_grupo_cliente.get("activo", 1))
    orden = _validar_orden(datos_grupo_cliente.get("orden", 0))
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                UPDATE grupos_clientes
                SET
                    nombre = ?,
                    activo = ?,
                    orden = ?,
                    actualizado_en = ?
                WHERE id = ?
                """,
                (
                    nombre,
                    activo,
                    orden,
                    actualizado_en,
                    grupo_cliente_id_validado,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo actualizar el grupo de clientes. Revise el nombre informado."
        ) from exc

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el grupo de clientes.")

    grupo = obtener_grupo_cliente_por_id(grupo_cliente_id_validado)

    if grupo is None:
        raise ValueError("No se pudo recuperar el grupo de clientes actualizado.")

    return grupo


def cambiar_estado_grupo_cliente(
    grupo_cliente_id: Any,
    activo: Any,
) -> dict[str, Any]:
    """Activa o desactiva un grupo de clientes sin borrado fisico."""
    grupo_cliente_id_validado = _validar_id_grupo_cliente(grupo_cliente_id)
    activo_validado = _validar_activo(activo)

    if obtener_grupo_cliente_por_id(grupo_cliente_id_validado) is None:
        raise ValueError("No existe el grupo de clientes informado.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE grupos_clientes
            SET activo = ?, actualizado_en = ?
            WHERE id = ?
            """,
            (activo_validado, actualizado_en, grupo_cliente_id_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el estado del grupo de clientes.")

    grupo = obtener_grupo_cliente_por_id(grupo_cliente_id_validado)

    if grupo is None:
        raise ValueError("No se pudo recuperar el grupo de clientes actualizado.")

    return grupo


def validar_grupo_cliente_activo(grupo_cliente_id: Any) -> bool:
    """Valida que un grupo de clientes exista y este activo."""
    grupo_cliente_id_validado = _validar_id_grupo_cliente(grupo_cliente_id)

    fila_grupo = get_db().execute(
        """
        SELECT 1
        FROM grupos_clientes
        WHERE id = ?
          AND activo = 1
        LIMIT 1
        """,
        (grupo_cliente_id_validado,),
    ).fetchone()

    if fila_grupo is None:
        raise ValueError("El grupo de clientes no existe o no esta activo.")

    return True


def _normalizar_fila_grupo_cliente(fila_grupo) -> dict[str, Any]:
    """Convierte una fila SQLite de grupos_clientes en dict explicito."""
    grupo = dict(fila_grupo)

    grupo["id"] = int(grupo["id"])
    grupo["activo"] = int(grupo["activo"])
    grupo["orden"] = int(grupo["orden"])
    grupo["esta_activo"] = grupo["activo"] == 1
    grupo["descripcion_select"] = grupo["nombre"]

    return grupo


def _validar_id_grupo_cliente(grupo_cliente_id: Any) -> int:
    try:
        grupo_cliente_id_validado = int(str(grupo_cliente_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del grupo de clientes debe ser numerico.") from exc

    if grupo_cliente_id_validado <= 0:
        raise ValueError("El id del grupo de clientes debe ser positivo.")

    return grupo_cliente_id_validado


def _validar_nombre_grupo_cliente(nombre: Any) -> str:
    nombre_validado = str(nombre or "").strip()

    if not nombre_validado:
        raise ValueError("El nombre del grupo de clientes es obligatorio.")

    return nombre_validado


def _validar_activo(activo: Any) -> int:
    if isinstance(activo, bool):
        return 1 if activo else 0

    if isinstance(activo, int) and activo in (0, 1):
        return activo

    activo_normalizado = str(activo or "").strip()

    if activo_normalizado in {"0", "1"}:
        return int(activo_normalizado)

    raise ValueError("El estado activo del grupo de clientes es invalido.")


def _validar_orden(orden: Any) -> int:
    try:
        orden_validado = int(str(orden or "0").strip())
    except ValueError as exc:
        raise ValueError("El orden del grupo de clientes debe ser numerico.") from exc

    if orden_validado < 0:
        raise ValueError("El orden del grupo de clientes no puede ser negativo.")

    return orden_validado
