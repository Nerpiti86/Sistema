import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db


_CATALOGOS = {
    "condiciones_iva": {
        "tabla": "condiciones_iva",
        "nombre_error": "condicion frente al IVA",
    },
    "tipos_documento": {
        "tabla": "tipos_documento",
        "nombre_error": "tipo de documento",
    },
    "unidades_medida": {
        "tabla": "unidades_medida",
        "nombre_error": "unidad de medida",
    },
    "tipos_bonificacion": {
        "tabla": "tipos_bonificacion",
        "nombre_error": "tipo de bonificacion",
    },
    "tipos_comprobante": {
        "tabla": "tipos_comprobante",
        "nombre_error": "tipo de comprobante",
    },
}


def listar_catalogo_fiscal(catalogo: str) -> list[dict[str, Any]]:
    """Devuelve items de un catalogo fiscal ordenados por orden y codigo."""
    definicion = _obtener_definicion_catalogo(catalogo)
    tabla = definicion["tabla"]

    filas = get_db().execute(
        f"""
        SELECT id, codigo, descripcion, activo, orden, creado_en, actualizado_en
        FROM {tabla}
        ORDER BY orden, CAST(codigo AS INTEGER)
        """
    ).fetchall()

    return [_normalizar_fila(fila) for fila in filas]


def listar_catalogo_fiscal_activo(catalogo: str) -> list[dict[str, Any]]:
    """Devuelve items activos de un catalogo fiscal para formularios."""
    definicion = _obtener_definicion_catalogo(catalogo)
    tabla = definicion["tabla"]

    filas = get_db().execute(
        f"""
        SELECT id, codigo, descripcion, activo, orden, creado_en, actualizado_en
        FROM {tabla}
        WHERE activo = 1
        ORDER BY orden, CAST(codigo AS INTEGER)
        """
    ).fetchall()

    return [_normalizar_fila(fila) for fila in filas]


def obtener_item_catalogo_fiscal_por_codigo(
    catalogo: str,
    codigo: Any,
) -> dict[str, Any] | None:
    """Devuelve un item de catalogo fiscal por codigo, o None si no existe."""
    definicion = _obtener_definicion_catalogo(catalogo)
    tabla = definicion["tabla"]
    codigo_validado = _validar_codigo(codigo, definicion["nombre_error"])

    fila = get_db().execute(
        f"""
        SELECT id, codigo, descripcion, activo, orden, creado_en, actualizado_en
        FROM {tabla}
        WHERE codigo = ?
        LIMIT 1
        """,
        (codigo_validado,),
    ).fetchone()

    if fila is None:
        return None

    return _normalizar_fila(fila)


def crear_item_catalogo_fiscal(
    catalogo: str,
    datos: dict[str, Any],
) -> dict[str, Any]:
    """Inserta un item de catalogo fiscal y devuelve la fila creada."""
    definicion = _obtener_definicion_catalogo(catalogo)
    tabla = definicion["tabla"]
    nombre_error = definicion["nombre_error"]
    codigo = _validar_codigo(datos["codigo"], nombre_error)
    descripcion = _validar_descripcion(datos["descripcion"], nombre_error)
    activo = _validar_activo(datos.get("activo", 1), nombre_error)
    orden = _validar_orden(datos.get("orden", 0), nombre_error)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            db.execute(
                f"""
                INSERT INTO {tabla} (codigo, descripcion, activo, orden, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (codigo, descripcion, activo, orden, creado_en),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"No se pudo crear la {nombre_error}. Revise el codigo informado.") from exc

    item = obtener_item_catalogo_fiscal_por_codigo(catalogo, codigo)

    if item is None:
        raise ValueError(f"No se pudo recuperar la {nombre_error} creada.")

    return item


def actualizar_item_catalogo_fiscal_por_codigo(
    catalogo: str,
    codigo: Any,
    datos: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de un item de catalogo fiscal."""
    definicion = _obtener_definicion_catalogo(catalogo)
    tabla = definicion["tabla"]
    nombre_error = definicion["nombre_error"]
    codigo_validado = _validar_codigo(codigo, nombre_error)

    if obtener_item_catalogo_fiscal_por_codigo(catalogo, codigo_validado) is None:
        raise ValueError(f"No existe la {nombre_error} informada.")

    descripcion = _validar_descripcion(datos["descripcion"], nombre_error)
    activo = _validar_activo(datos.get("activo", 1), nombre_error)
    orden = _validar_orden(datos.get("orden", 0), nombre_error)
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    with db:
        cursor = db.execute(
            f"""
            UPDATE {tabla}
            SET descripcion = ?, activo = ?, orden = ?, actualizado_en = ?
            WHERE codigo = ?
            """,
            (descripcion, activo, orden, actualizado_en, codigo_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError(f"No se pudo actualizar la {nombre_error}.")

    item = obtener_item_catalogo_fiscal_por_codigo(catalogo, codigo_validado)

    if item is None:
        raise ValueError(f"No se pudo recuperar la {nombre_error} actualizada.")

    return item


def cambiar_estado_item_catalogo_fiscal(
    catalogo: str,
    codigo: Any,
    activo: Any,
) -> dict[str, Any]:
    """Activa o desactiva un item de catalogo fiscal sin borrado fisico."""
    definicion = _obtener_definicion_catalogo(catalogo)
    tabla = definicion["tabla"]
    nombre_error = definicion["nombre_error"]
    codigo_validado = _validar_codigo(codigo, nombre_error)
    activo_validado = _validar_activo(activo, nombre_error)

    if obtener_item_catalogo_fiscal_por_codigo(catalogo, codigo_validado) is None:
        raise ValueError(f"No existe la {nombre_error} informada.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            f"""
            UPDATE {tabla}
            SET activo = ?, actualizado_en = ?
            WHERE codigo = ?
            """,
            (activo_validado, actualizado_en, codigo_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError(f"No se pudo actualizar el estado de la {nombre_error}.")

    item = obtener_item_catalogo_fiscal_por_codigo(catalogo, codigo_validado)

    if item is None:
        raise ValueError(f"No se pudo recuperar la {nombre_error} actualizada.")

    return item


def validar_item_catalogo_fiscal_activo(catalogo: str, codigo: Any) -> bool:
    """Valida que un item exista y este activo."""
    definicion = _obtener_definicion_catalogo(catalogo)
    tabla = definicion["tabla"]
    nombre_error = definicion["nombre_error"]
    codigo_validado = _validar_codigo(codigo, nombre_error)

    fila = get_db().execute(
        f"""
        SELECT 1
        FROM {tabla}
        WHERE codigo = ? AND activo = 1
        LIMIT 1
        """,
        (codigo_validado,),
    ).fetchone()

    if fila is None:
        raise ValueError(f"La {nombre_error} no existe o no esta activa.")

    return True


def _obtener_definicion_catalogo(catalogo: str) -> dict[str, str]:
    try:
        return _CATALOGOS[catalogo]
    except KeyError as exc:
        raise ValueError("Catalogo fiscal invalido.") from exc


def _normalizar_fila(fila) -> dict[str, Any]:
    item = dict(fila)
    item["activo"] = int(item["activo"])
    item["orden"] = int(item["orden"])
    item["esta_activo"] = item["activo"] == 1
    item["descripcion_select"] = f"{item['codigo']} - {item['descripcion']}"
    return item


def _validar_codigo(codigo: Any, nombre_error: str) -> str:
    codigo_validado = str(codigo or "").strip()

    if not codigo_validado:
        raise ValueError(f"El codigo de {nombre_error} es obligatorio.")

    if len(codigo_validado) > 3 or not codigo_validado.isdigit():
        raise ValueError(f"El codigo de {nombre_error} debe ser numerico de hasta 3 digitos.")

    return codigo_validado


def _validar_descripcion(descripcion: Any, nombre_error: str) -> str:
    descripcion_validada = str(descripcion or "").strip()

    if not descripcion_validada:
        raise ValueError(f"La descripcion de {nombre_error} es obligatoria.")

    return descripcion_validada


def _validar_activo(activo: Any, nombre_error: str) -> int:
    if isinstance(activo, bool):
        return 1 if activo else 0

    if isinstance(activo, int) and activo in (0, 1):
        return activo

    activo_normalizado = str(activo or "").strip()

    if activo_normalizado in {"0", "1"}:
        return int(activo_normalizado)

    raise ValueError(f"El estado activo de {nombre_error} es invalido.")


def _validar_orden(orden: Any, nombre_error: str) -> int:
    try:
        orden_validado = int(str(orden or "0").strip())
    except ValueError as exc:
        raise ValueError(f"El orden de {nombre_error} debe ser numerico.") from exc

    if orden_validado < 0:
        raise ValueError(f"El orden de {nombre_error} no puede ser negativo.")

    return orden_validado
