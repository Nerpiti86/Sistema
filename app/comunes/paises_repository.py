import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_PAISES = """
    id,
    nombre,
    codigo_iso,
    activo,
    orden,
    creado_en,
    actualizado_en
"""


def listar_paises() -> list[dict[str, Any]]:
    """
    Devuelve paises ordenados para gestion.

    El maestro no se pagina en esta etapa porque se espera un catalogo chico de
    paises usados operativamente.
    """
    filas_paises = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_PAISES}
        FROM paises
        ORDER BY activo DESC, orden, nombre
        """
    ).fetchall()

    return [_normalizar_fila_pais(fila_pais) for fila_pais in filas_paises]


def listar_paises_activos() -> list[dict[str, Any]]:
    """Devuelve paises activos ordenados para selects de gestion."""
    filas_paises = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_PAISES}
        FROM paises
        WHERE activo = 1
        ORDER BY orden, nombre
        """
    ).fetchall()

    return [_normalizar_fila_pais(fila_pais) for fila_pais in filas_paises]


def obtener_pais_por_id(pais_id: Any) -> dict[str, Any] | None:
    """Devuelve un pais por id, o None si no existe."""
    pais_id_validado = _validar_id_pais(pais_id)

    fila_pais = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_PAISES}
        FROM paises
        WHERE id = ?
        LIMIT 1
        """,
        (pais_id_validado,),
    ).fetchone()

    if fila_pais is None:
        return None

    return _normalizar_fila_pais(fila_pais)


def crear_pais(datos_pais: dict[str, Any]) -> dict[str, Any]:
    """Inserta un pais y devuelve la fila creada."""
    nombre = _validar_nombre_pais(datos_pais["nombre"])
    codigo_iso = _normalizar_codigo_iso(datos_pais.get("codigo_iso"))
    activo = _validar_activo(datos_pais.get("activo", 1))
    orden = _validar_orden(datos_pais.get("orden", 0))
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                INSERT INTO paises (
                    nombre,
                    codigo_iso,
                    activo,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (nombre, codigo_iso, activo, orden, creado_en),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear el pais. Revise el nombre o codigo ISO informado."
        ) from exc

    pais = obtener_pais_por_id(cursor.lastrowid)

    if pais is None:
        raise ValueError("No se pudo recuperar el pais creado.")

    return pais


def actualizar_pais_por_id(
    pais_id: Any,
    datos_pais: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de un pais y devuelve la fila final."""
    pais_id_validado = _validar_id_pais(pais_id)

    if obtener_pais_por_id(pais_id_validado) is None:
        raise ValueError("No existe el pais informado.")

    nombre = _validar_nombre_pais(datos_pais["nombre"])
    codigo_iso = _normalizar_codigo_iso(datos_pais.get("codigo_iso"))
    activo = _validar_activo(datos_pais.get("activo", 1))
    orden = _validar_orden(datos_pais.get("orden", 0))
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                UPDATE paises
                SET
                    nombre = ?,
                    codigo_iso = ?,
                    activo = ?,
                    orden = ?,
                    actualizado_en = ?
                WHERE id = ?
                """,
                (
                    nombre,
                    codigo_iso,
                    activo,
                    orden,
                    actualizado_en,
                    pais_id_validado,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo actualizar el pais. Revise el nombre o codigo ISO informado."
        ) from exc

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el pais.")

    pais = obtener_pais_por_id(pais_id_validado)

    if pais is None:
        raise ValueError("No se pudo recuperar el pais actualizado.")

    return pais


def cambiar_estado_pais(
    pais_id: Any,
    activo: Any,
) -> dict[str, Any]:
    """Activa o desactiva un pais sin borrado fisico."""
    pais_id_validado = _validar_id_pais(pais_id)
    activo_validado = _validar_activo(activo)

    if obtener_pais_por_id(pais_id_validado) is None:
        raise ValueError("No existe el pais informado.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE paises
            SET activo = ?, actualizado_en = ?
            WHERE id = ?
            """,
            (activo_validado, actualizado_en, pais_id_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el estado del pais.")

    pais = obtener_pais_por_id(pais_id_validado)

    if pais is None:
        raise ValueError("No se pudo recuperar el pais actualizado.")

    return pais


def validar_pais_activo(pais_id: Any) -> bool:
    """Valida que un pais exista y este activo."""
    pais_id_validado = _validar_id_pais(pais_id)

    fila_pais = get_db().execute(
        """
        SELECT 1
        FROM paises
        WHERE id = ?
          AND activo = 1
        LIMIT 1
        """,
        (pais_id_validado,),
    ).fetchone()

    if fila_pais is None:
        raise ValueError("El pais no existe o no esta activo.")

    return True


def _normalizar_fila_pais(fila_pais) -> dict[str, Any]:
    """Convierte una fila SQLite de paises en dict explicito."""
    pais = dict(fila_pais)

    pais["id"] = int(pais["id"])
    pais["activo"] = int(pais["activo"])
    pais["orden"] = int(pais["orden"])
    pais["esta_activo"] = pais["activo"] == 1

    if pais["codigo_iso"]:
        pais["descripcion_select"] = f"{pais['nombre']} ({pais['codigo_iso']})"
    else:
        pais["descripcion_select"] = pais["nombre"]

    return pais


def _validar_id_pais(pais_id: Any) -> int:
    try:
        pais_id_validado = int(str(pais_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del pais debe ser numerico.") from exc

    if pais_id_validado <= 0:
        raise ValueError("El id del pais debe ser positivo.")

    return pais_id_validado


def _validar_nombre_pais(nombre: Any) -> str:
    nombre_validado = str(nombre or "").strip()

    if not nombre_validado:
        raise ValueError("El nombre del pais es obligatorio.")

    return nombre_validado


def _normalizar_codigo_iso(codigo_iso: Any) -> str | None:
    codigo_iso_normalizado = str(codigo_iso or "").strip().upper()

    if not codigo_iso_normalizado:
        return None

    if len(codigo_iso_normalizado) not in (2, 3):
        raise ValueError("El codigo ISO del pais debe tener 2 o 3 caracteres.")

    return codigo_iso_normalizado


def _validar_activo(activo: Any) -> int:
    if isinstance(activo, bool):
        return 1 if activo else 0

    if isinstance(activo, int) and activo in (0, 1):
        return activo

    activo_normalizado = str(activo or "").strip()

    if activo_normalizado in {"0", "1"}:
        return int(activo_normalizado)

    raise ValueError("El estado activo del pais es invalido.")


def _validar_orden(orden: Any) -> int:
    try:
        orden_validado = int(str(orden or "0").strip())
    except ValueError as exc:
        raise ValueError("El orden del pais debe ser numerico.") from exc

    if orden_validado < 0:
        raise ValueError("El orden del pais no puede ser negativo.")

    return orden_validado
