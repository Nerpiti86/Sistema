import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_ARTICULOS_VENTA = """
    articulos_venta.id,
    articulos_venta.nombre,
    articulos_venta.tipo,
    articulos_venta.moneda_codigo,
    articulos_venta.precio_unitario_sugerido_1000000,
    articulos_venta.cuenta_ingreso_codigo,
    articulos_venta.activo,
    articulos_venta.orden,
    articulos_venta.observaciones,
    articulos_venta.creado_en,
    articulos_venta.actualizado_en,
    monedas.nombre AS moneda_nombre,
    monedas.simbolo AS moneda_simbolo,
    monedas.decimales AS moneda_decimales,
    cuentas_contables.descripcion AS cuenta_ingreso_descripcion
"""


def listar_articulos_venta() -> list[dict[str, Any]]:
    """
    Devuelve productos o servicios vendibles ordenados para gestion.

    El maestro se mantiene sin paginar en esta etapa inicial. Si el volumen
    crece, el repository debera incorporar filtros y paginacion SQL.
    """
    filas_articulos = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_ARTICULOS_VENTA}
        FROM articulos_venta
        JOIN monedas
          ON monedas.codigo = articulos_venta.moneda_codigo
        LEFT JOIN cuentas_contables
          ON cuentas_contables.cuenta = articulos_venta.cuenta_ingreso_codigo
        ORDER BY articulos_venta.activo DESC,
                 articulos_venta.orden,
                 articulos_venta.nombre
        """
    ).fetchall()

    return [
        _normalizar_fila_articulo_venta(fila_articulo)
        for fila_articulo in filas_articulos
    ]


def listar_articulos_venta_activos() -> list[dict[str, Any]]:
    """Devuelve productos o servicios activos ordenados para selects y operaciones."""
    filas_articulos = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_ARTICULOS_VENTA}
        FROM articulos_venta
        JOIN monedas
          ON monedas.codigo = articulos_venta.moneda_codigo
        LEFT JOIN cuentas_contables
          ON cuentas_contables.cuenta = articulos_venta.cuenta_ingreso_codigo
        WHERE articulos_venta.activo = 1
        ORDER BY articulos_venta.orden,
                 articulos_venta.nombre
        """
    ).fetchall()

    return [
        _normalizar_fila_articulo_venta(fila_articulo)
        for fila_articulo in filas_articulos
    ]


def obtener_articulo_venta_por_id(articulo_venta_id: Any) -> dict[str, Any] | None:
    """Devuelve un producto o servicio vendible por id, o None si no existe."""
    articulo_venta_id_validado = _validar_id_articulo_venta(articulo_venta_id)

    fila_articulo = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_ARTICULOS_VENTA}
        FROM articulos_venta
        JOIN monedas
          ON monedas.codigo = articulos_venta.moneda_codigo
        LEFT JOIN cuentas_contables
          ON cuentas_contables.cuenta = articulos_venta.cuenta_ingreso_codigo
        WHERE articulos_venta.id = ?
        LIMIT 1
        """,
        (articulo_venta_id_validado,),
    ).fetchone()

    if fila_articulo is None:
        return None

    return _normalizar_fila_articulo_venta(fila_articulo)


def crear_articulo_venta(datos_articulo: dict[str, Any]) -> dict[str, Any]:
    """Inserta un producto o servicio vendible y devuelve la fila creada."""
    datos_validados = _validar_datos_articulo_venta(datos_articulo)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    precio_unitario_sugerido_1000000,
                    cuenta_ingreso_codigo,
                    activo,
                    orden,
                    observaciones,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos_validados["nombre"],
                    datos_validados["tipo"],
                    datos_validados["moneda_codigo"],
                    datos_validados["precio_unitario_sugerido_1000000"],
                    datos_validados["cuenta_ingreso_codigo"],
                    datos_validados["activo"],
                    datos_validados["orden"],
                    datos_validados["observaciones"],
                    creado_en,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear el producto o servicio. Revise nombre duplicado, "
            "moneda, cuenta de ingreso o datos invalidos."
        ) from exc

    articulo = obtener_articulo_venta_por_id(cursor.lastrowid)

    if articulo is None:
        raise ValueError("No se pudo recuperar el producto o servicio creado.")

    return articulo


def actualizar_articulo_venta_por_id(
    articulo_venta_id: Any,
    datos_articulo: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de un producto o servicio y devuelve la fila final."""
    articulo_venta_id_validado = _validar_id_articulo_venta(articulo_venta_id)

    if obtener_articulo_venta_por_id(articulo_venta_id_validado) is None:
        raise ValueError("No existe el producto o servicio informado.")

    datos_validados = _validar_datos_articulo_venta(datos_articulo)
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                UPDATE articulos_venta
                SET
                    nombre = ?,
                    tipo = ?,
                    moneda_codigo = ?,
                    precio_unitario_sugerido_1000000 = ?,
                    cuenta_ingreso_codigo = ?,
                    activo = ?,
                    orden = ?,
                    observaciones = ?,
                    actualizado_en = ?
                WHERE id = ?
                """,
                (
                    datos_validados["nombre"],
                    datos_validados["tipo"],
                    datos_validados["moneda_codigo"],
                    datos_validados["precio_unitario_sugerido_1000000"],
                    datos_validados["cuenta_ingreso_codigo"],
                    datos_validados["activo"],
                    datos_validados["orden"],
                    datos_validados["observaciones"],
                    actualizado_en,
                    articulo_venta_id_validado,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo actualizar el producto o servicio. Revise nombre duplicado, "
            "moneda, cuenta de ingreso o datos invalidos."
        ) from exc

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el producto o servicio.")

    articulo = obtener_articulo_venta_por_id(articulo_venta_id_validado)

    if articulo is None:
        raise ValueError("No se pudo recuperar el producto o servicio actualizado.")

    return articulo


def cambiar_estado_articulo_venta(
    articulo_venta_id: Any,
    activo: Any,
) -> dict[str, Any]:
    """Activa o desactiva un producto o servicio sin borrado fisico."""
    articulo_venta_id_validado = _validar_id_articulo_venta(articulo_venta_id)
    activo_validado = _validar_activo(activo)

    if obtener_articulo_venta_por_id(articulo_venta_id_validado) is None:
        raise ValueError("No existe el producto o servicio informado.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE articulos_venta
            SET activo = ?, actualizado_en = ?
            WHERE id = ?
            """,
            (activo_validado, actualizado_en, articulo_venta_id_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el estado del producto o servicio.")

    articulo = obtener_articulo_venta_por_id(articulo_venta_id_validado)

    if articulo is None:
        raise ValueError("No se pudo recuperar el producto o servicio actualizado.")

    return articulo


def validar_articulo_venta_activo(articulo_venta_id: Any) -> bool:
    """Valida que un producto o servicio exista y este activo."""
    articulo_venta_id_validado = _validar_id_articulo_venta(articulo_venta_id)

    fila_articulo = get_db().execute(
        """
        SELECT 1
        FROM articulos_venta
        WHERE id = ?
          AND activo = 1
        LIMIT 1
        """,
        (articulo_venta_id_validado,),
    ).fetchone()

    if fila_articulo is None:
        raise ValueError("El producto o servicio no existe o no esta activo.")

    return True


def _normalizar_fila_articulo_venta(fila_articulo) -> dict[str, Any]:
    """Convierte una fila SQLite de articulos_venta en dict explicito."""
    articulo = dict(fila_articulo)

    articulo["id"] = int(articulo["id"])
    articulo["precio_unitario_sugerido_1000000"] = int(
        articulo["precio_unitario_sugerido_1000000"]
    )
    articulo["activo"] = int(articulo["activo"])
    articulo["orden"] = int(articulo["orden"])
    articulo["esta_activo"] = articulo["activo"] == 1
    articulo["descripcion_select"] = articulo["nombre"]
    articulo["tipo_descripcion"] = _describir_tipo_articulo_venta(articulo["tipo"])

    if articulo.get("moneda_decimales") is not None:
        articulo["moneda_decimales"] = int(articulo["moneda_decimales"])

    return articulo


def _describir_tipo_articulo_venta(tipo: str) -> str:
    if tipo == "PRODUCTO":
        return "Producto"

    if tipo == "SERVICIO":
        return "Servicio"

    return tipo


def _validar_datos_articulo_venta(datos_articulo: dict[str, Any]) -> dict[str, Any]:
    return {
        "nombre": _validar_texto_obligatorio(
            datos_articulo.get("nombre"),
            "El nombre del producto o servicio es obligatorio.",
        ),
        "tipo": _validar_tipo_articulo_venta(datos_articulo.get("tipo")),
        "moneda_codigo": _validar_codigo_moneda(datos_articulo.get("moneda_codigo")),
        "precio_unitario_sugerido_1000000": _validar_entero_no_negativo(
            datos_articulo.get("precio_unitario_sugerido_1000000", 0),
            "El precio sugerido debe ser numerico.",
            "El precio sugerido no puede ser negativo.",
        ),
        "cuenta_ingreso_codigo": _validar_texto_opcional(
            datos_articulo.get("cuenta_ingreso_codigo")
        ),
        "activo": _validar_activo(datos_articulo.get("activo", 1)),
        "orden": _validar_entero_no_negativo(
            datos_articulo.get("orden", 0),
            "El orden del producto o servicio debe ser numerico.",
            "El orden del producto o servicio no puede ser negativo.",
        ),
        "observaciones": _validar_texto_opcional(datos_articulo.get("observaciones")),
    }


def _validar_id_articulo_venta(articulo_venta_id: Any) -> int:
    try:
        articulo_venta_id_validado = int(str(articulo_venta_id).strip())
    except ValueError as exc:
        raise ValueError("El id del producto o servicio debe ser numerico.") from exc

    if articulo_venta_id_validado <= 0:
        raise ValueError("El id del producto o servicio debe ser positivo.")

    return articulo_venta_id_validado


def _validar_tipo_articulo_venta(tipo: Any) -> str:
    tipo_validado = str(tipo or "").strip().upper()

    if tipo_validado not in {"PRODUCTO", "SERVICIO"}:
        raise ValueError("El tipo del producto o servicio es invalido.")

    return tipo_validado


def _validar_codigo_moneda(moneda_codigo: Any) -> str:
    moneda_codigo_validado = str(moneda_codigo or "").strip().upper()

    if not moneda_codigo_validado:
        raise ValueError("La moneda del producto o servicio es obligatoria.")

    return moneda_codigo_validado


def _validar_entero_no_negativo(
    valor: Any,
    mensaje_tipo: str,
    mensaje_negativo: str,
) -> int:
    try:
        valor_validado = int(str(valor or "0").strip())
    except ValueError as exc:
        raise ValueError(mensaje_tipo) from exc

    if valor_validado < 0:
        raise ValueError(mensaje_negativo)

    return valor_validado


def _validar_texto_obligatorio(valor: Any, mensaje_error: str) -> str:
    valor_validado = str(valor or "").strip()

    if not valor_validado:
        raise ValueError(mensaje_error)

    return valor_validado


def _validar_texto_opcional(valor: Any) -> str | None:
    valor_validado = str(valor or "").strip()

    if not valor_validado:
        return None

    return valor_validado


def _validar_activo(activo: Any) -> int:
    if isinstance(activo, bool):
        return 1 if activo else 0

    if isinstance(activo, int) and activo in (0, 1):
        return activo

    activo_normalizado = str(activo or "").strip()

    if activo_normalizado in {"0", "1"}:
        return int(activo_normalizado)

    raise ValueError("El estado activo del producto o servicio es invalido.")
