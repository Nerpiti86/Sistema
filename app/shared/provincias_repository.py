import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_PROVINCIAS = """
    provincias.id,
    provincias.pais_id,
    provincias.nombre,
    provincias.activo,
    provincias.orden,
    provincias.creado_en,
    provincias.actualizado_en,
    paises.nombre AS pais_nombre,
    paises.codigo_iso AS pais_codigo_iso
"""


def listar_provincias() -> list[dict[str, Any]]:
    """
    Devuelve provincias ordenadas para uso transversal.

    La tabla provincias depende de paises y se usa como maestro comun para
    domicilios, clientes, proveedores y datos fiscales.
    """
    filas_provincias = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_PROVINCIAS}
        FROM provincias
        JOIN paises ON paises.id = provincias.pais_id
        ORDER BY paises.nombre, provincias.activo DESC, provincias.orden, provincias.nombre
        """
    ).fetchall()

    return [
        _normalizar_fila_provincia(fila_provincia)
        for fila_provincia in filas_provincias
    ]


def listar_provincias_por_pais(pais_id: Any) -> list[dict[str, Any]]:
    """Devuelve provincias de un pais ordenadas para gestion."""
    pais_id_validado = _validar_id_pais(pais_id)

    filas_provincias = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_PROVINCIAS}
        FROM provincias
        JOIN paises ON paises.id = provincias.pais_id
        WHERE provincias.pais_id = ?
        ORDER BY provincias.activo DESC, provincias.orden, provincias.nombre
        """,
        (pais_id_validado,),
    ).fetchall()

    return [
        _normalizar_fila_provincia(fila_provincia)
        for fila_provincia in filas_provincias
    ]


def listar_provincias_activas_por_pais(pais_id: Any) -> list[dict[str, Any]]:
    """Devuelve provincias activas de un pais ordenadas para selects."""
    pais_id_validado = _validar_id_pais(pais_id)

    filas_provincias = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_PROVINCIAS}
        FROM provincias
        JOIN paises ON paises.id = provincias.pais_id
        WHERE provincias.pais_id = ?
          AND provincias.activo = 1
        ORDER BY provincias.orden, provincias.nombre
        """,
        (pais_id_validado,),
    ).fetchall()

    return [
        _normalizar_fila_provincia(fila_provincia)
        for fila_provincia in filas_provincias
    ]


def obtener_provincia_por_id(provincia_id: Any) -> dict[str, Any] | None:
    """Devuelve una provincia por id, o None si no existe."""
    provincia_id_validado = _validar_id_provincia(provincia_id)

    fila_provincia = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_PROVINCIAS}
        FROM provincias
        JOIN paises ON paises.id = provincias.pais_id
        WHERE provincias.id = ?
        LIMIT 1
        """,
        (provincia_id_validado,),
    ).fetchone()

    if fila_provincia is None:
        return None

    return _normalizar_fila_provincia(fila_provincia)


def crear_provincia(datos_provincia: dict[str, Any]) -> dict[str, Any]:
    """Inserta una provincia y devuelve la fila creada."""
    pais_id = _validar_id_pais(datos_provincia["pais_id"])
    nombre = _validar_nombre_provincia(datos_provincia["nombre"])
    activo = _validar_activo(datos_provincia.get("activo", 1))
    orden = _validar_orden(datos_provincia.get("orden", 0))
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                INSERT INTO provincias (
                    pais_id,
                    nombre,
                    activo,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (pais_id, nombre, activo, orden, creado_en),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear la provincia. Revise el pais y nombre informado."
        ) from exc

    provincia = obtener_provincia_por_id(cursor.lastrowid)

    if provincia is None:
        raise ValueError("No se pudo recuperar la provincia creada.")

    return provincia


def actualizar_provincia_por_id(
    provincia_id: Any,
    datos_provincia: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de una provincia y devuelve la fila final."""
    provincia_id_validado = _validar_id_provincia(provincia_id)

    if obtener_provincia_por_id(provincia_id_validado) is None:
        raise ValueError("No existe la provincia informada.")

    pais_id = _validar_id_pais(datos_provincia["pais_id"])
    nombre = _validar_nombre_provincia(datos_provincia["nombre"])
    activo = _validar_activo(datos_provincia.get("activo", 1))
    orden = _validar_orden(datos_provincia.get("orden", 0))
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                UPDATE provincias
                SET
                    pais_id = ?,
                    nombre = ?,
                    activo = ?,
                    orden = ?,
                    actualizado_en = ?
                WHERE id = ?
                """,
                (
                    pais_id,
                    nombre,
                    activo,
                    orden,
                    actualizado_en,
                    provincia_id_validado,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo actualizar la provincia. Revise el pais y nombre informado."
        ) from exc

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar la provincia.")

    provincia = obtener_provincia_por_id(provincia_id_validado)

    if provincia is None:
        raise ValueError("No se pudo recuperar la provincia actualizada.")

    return provincia


def cambiar_estado_provincia(
    provincia_id: Any,
    activo: Any,
) -> dict[str, Any]:
    """Activa o desactiva una provincia sin borrado fisico."""
    provincia_id_validado = _validar_id_provincia(provincia_id)
    activo_validado = _validar_activo(activo)

    if obtener_provincia_por_id(provincia_id_validado) is None:
        raise ValueError("No existe la provincia informada.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE provincias
            SET activo = ?, actualizado_en = ?
            WHERE id = ?
            """,
            (activo_validado, actualizado_en, provincia_id_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el estado de la provincia.")

    provincia = obtener_provincia_por_id(provincia_id_validado)

    if provincia is None:
        raise ValueError("No se pudo recuperar la provincia actualizada.")

    return provincia


def validar_provincia_activa(provincia_id: Any) -> bool:
    """Valida que una provincia exista y este activa."""
    provincia_id_validado = _validar_id_provincia(provincia_id)

    fila_provincia = get_db().execute(
        """
        SELECT 1
        FROM provincias
        WHERE id = ?
          AND activo = 1
        LIMIT 1
        """,
        (provincia_id_validado,),
    ).fetchone()

    if fila_provincia is None:
        raise ValueError("La provincia no existe o no esta activa.")

    return True


def _normalizar_fila_provincia(fila_provincia) -> dict[str, Any]:
    """Convierte una fila SQLite de provincias en dict explicito."""
    provincia = dict(fila_provincia)

    provincia["id"] = int(provincia["id"])
    provincia["pais_id"] = int(provincia["pais_id"])
    provincia["activo"] = int(provincia["activo"])
    provincia["orden"] = int(provincia["orden"])
    provincia["esta_activa"] = provincia["activo"] == 1

    if provincia.get("pais_codigo_iso"):
        provincia["pais_descripcion"] = (
            f"{provincia['pais_nombre']} ({provincia['pais_codigo_iso']})"
        )
    else:
        provincia["pais_descripcion"] = provincia["pais_nombre"]

    provincia["descripcion_select"] = provincia["nombre"]

    return provincia


def _validar_id_provincia(provincia_id: Any) -> int:
    try:
        provincia_id_validado = int(str(provincia_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id de la provincia debe ser numerico.") from exc

    if provincia_id_validado <= 0:
        raise ValueError("El id de la provincia debe ser positivo.")

    return provincia_id_validado


def _validar_id_pais(pais_id: Any) -> int:
    try:
        pais_id_validado = int(str(pais_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del pais debe ser numerico.") from exc

    if pais_id_validado <= 0:
        raise ValueError("El id del pais debe ser positivo.")

    return pais_id_validado


def _validar_nombre_provincia(nombre: Any) -> str:
    nombre_validado = str(nombre or "").strip()

    if not nombre_validado:
        raise ValueError("El nombre de la provincia es obligatorio.")

    return nombre_validado


def _validar_activo(activo: Any) -> int:
    if isinstance(activo, bool):
        return 1 if activo else 0

    if isinstance(activo, int) and activo in (0, 1):
        return activo

    activo_normalizado = str(activo or "").strip()

    if activo_normalizado in {"0", "1"}:
        return int(activo_normalizado)

    raise ValueError("El estado activo de la provincia es invalido.")


def _validar_orden(orden: Any) -> int:
    try:
        orden_validado = int(str(orden or "0").strip())
    except ValueError as exc:
        raise ValueError("El orden de la provincia debe ser numerico.") from exc

    if orden_validado < 0:
        raise ValueError("El orden de la provincia no puede ser negativo.")

    return orden_validado
