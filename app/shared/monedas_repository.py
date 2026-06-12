import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_MONEDAS = """
    id,
    codigo,
    nombre,
    simbolo,
    decimales,
    activa,
    orden,
    creado_en,
    actualizado_en
"""


def listar_monedas() -> list[dict[str, Any]]:
    """
    Devuelve monedas ordenadas para uso transversal.

    La tabla monedas es un maestro chico compartido por gestion, contabilidad,
    tesoreria y reportes. No corresponde paginarla en esta etapa.
    """
    filas_monedas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS}
        FROM monedas
        ORDER BY orden, codigo
        """
    ).fetchall()

    return [_normalizar_fila_moneda(fila_moneda) for fila_moneda in filas_monedas]


def listar_monedas_activas() -> list[dict[str, Any]]:
    """Devuelve monedas activas ordenadas para selects y operaciones."""
    filas_monedas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS}
        FROM monedas
        WHERE activa = 1
        ORDER BY orden, codigo
        """
    ).fetchall()

    return [_normalizar_fila_moneda(fila_moneda) for fila_moneda in filas_monedas]


def obtener_moneda_por_codigo(codigo_moneda: Any) -> dict[str, Any] | None:
    """Devuelve una moneda por codigo, o None si no existe."""
    codigo_moneda_validado = _validar_codigo_moneda(codigo_moneda)

    fila_moneda = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS}
        FROM monedas
        WHERE codigo = ?
        LIMIT 1
        """,
        (codigo_moneda_validado,),
    ).fetchone()

    if fila_moneda is None:
        return None

    return _normalizar_fila_moneda(fila_moneda)


def crear_moneda(datos_moneda: dict[str, Any]) -> dict[str, Any]:
    """Inserta una moneda manual y devuelve la fila creada."""
    codigo = _validar_codigo_moneda(datos_moneda["codigo"])
    nombre = _validar_texto_obligatorio(
        datos_moneda["nombre"],
        "El nombre de la moneda es obligatorio.",
    )
    simbolo = _validar_texto_obligatorio(
        datos_moneda["simbolo"],
        "El simbolo de la moneda es obligatorio.",
    )
    decimales = _validar_decimales(datos_moneda.get("decimales", 2))
    activa = _validar_activa(datos_moneda.get("activa", 1))
    orden = _validar_orden(datos_moneda.get("orden", 0))
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            db.execute(
                """
                INSERT INTO monedas (
                    codigo,
                    nombre,
                    simbolo,
                    decimales,
                    activa,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (codigo, nombre, simbolo, decimales, activa, orden, creado_en),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo crear la moneda. Revise el codigo informado.") from exc

    moneda = obtener_moneda_por_codigo(codigo)

    if moneda is None:
        raise ValueError("No se pudo recuperar la moneda creada.")

    return moneda


def actualizar_moneda_por_codigo(
    codigo_moneda: Any,
    datos_moneda: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de una moneda y devuelve la fila final."""
    codigo_moneda_validado = _validar_codigo_moneda(codigo_moneda)

    if obtener_moneda_por_codigo(codigo_moneda_validado) is None:
        raise ValueError("No existe la moneda informada.")

    nombre = _validar_texto_obligatorio(
        datos_moneda["nombre"],
        "El nombre de la moneda es obligatorio.",
    )
    simbolo = _validar_texto_obligatorio(
        datos_moneda["simbolo"],
        "El simbolo de la moneda es obligatorio.",
    )
    decimales = _validar_decimales(datos_moneda.get("decimales", 2))
    activa = _validar_activa(datos_moneda.get("activa", 1))
    orden = _validar_orden(datos_moneda.get("orden", 0))
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE monedas
            SET
                nombre = ?,
                simbolo = ?,
                decimales = ?,
                activa = ?,
                orden = ?,
                actualizado_en = ?
            WHERE codigo = ?
            """,
            (
                nombre,
                simbolo,
                decimales,
                activa,
                orden,
                actualizado_en,
                codigo_moneda_validado,
            ),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar la moneda.")

    moneda = obtener_moneda_por_codigo(codigo_moneda_validado)

    if moneda is None:
        raise ValueError("No se pudo recuperar la moneda actualizada.")

    return moneda


def cambiar_estado_moneda(codigo_moneda: Any, activa: Any) -> dict[str, Any]:
    """Activa o desactiva una moneda sin borrarla fisicamente."""
    codigo_moneda_validado = _validar_codigo_moneda(codigo_moneda)
    activa_validada = _validar_activa(activa)

    if obtener_moneda_por_codigo(codigo_moneda_validado) is None:
        raise ValueError("No existe la moneda informada.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE monedas
            SET activa = ?, actualizado_en = ?
            WHERE codigo = ?
            """,
            (activa_validada, actualizado_en, codigo_moneda_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el estado de la moneda.")

    moneda = obtener_moneda_por_codigo(codigo_moneda_validado)

    if moneda is None:
        raise ValueError("No se pudo recuperar la moneda actualizada.")

    return moneda


def validar_moneda_activa(codigo_moneda: Any) -> bool:
    """Valida que una moneda exista y este activa."""
    codigo_moneda_validado = _validar_codigo_moneda(codigo_moneda)

    fila_moneda = get_db().execute(
        """
        SELECT 1
        FROM monedas
        WHERE codigo = ?
          AND activa = 1
        LIMIT 1
        """,
        (codigo_moneda_validado,),
    ).fetchone()

    if fila_moneda is None:
        raise ValueError("La moneda no existe o no esta activa.")

    return True


def _normalizar_fila_moneda(fila_moneda) -> dict[str, Any]:
    """Convierte una fila SQLite de monedas en dict explicito."""
    moneda = dict(fila_moneda)

    moneda["decimales"] = int(moneda["decimales"])
    moneda["activa"] = int(moneda["activa"])
    moneda["orden"] = int(moneda["orden"])
    moneda["esta_activa"] = moneda["activa"] == 1
    moneda["descripcion_select"] = (
        f"{moneda['codigo']} - {moneda['nombre']}"
    )

    return moneda


def _validar_codigo_moneda(codigo_moneda: Any) -> str:
    """Valida y normaliza codigo de moneda ISO de tres letras."""
    codigo_moneda_validado = str(codigo_moneda or "").strip().upper()

    if not codigo_moneda_validado:
        raise ValueError("El codigo de moneda es obligatorio.")

    if len(codigo_moneda_validado) != 3 or not codigo_moneda_validado.isalpha():
        raise ValueError("El codigo de moneda debe tener formato AAA.")

    return codigo_moneda_validado


def _validar_texto_obligatorio(valor: Any, mensaje_error: str) -> str:
    valor_validado = str(valor or "").strip()

    if not valor_validado:
        raise ValueError(mensaje_error)

    return valor_validado


def _validar_decimales(decimales: Any) -> int:
    try:
        decimales_validados = int(str(decimales or "0").strip())
    except ValueError as exc:
        raise ValueError("Los decimales de la moneda deben ser numericos.") from exc

    if decimales_validados < 0 or decimales_validados > 6:
        raise ValueError("Los decimales de la moneda deben estar entre 0 y 6.")

    return decimales_validados


def _validar_activa(activa: Any) -> int:
    if isinstance(activa, bool):
        return 1 if activa else 0

    if isinstance(activa, int) and activa in (0, 1):
        return activa

    activa_normalizada = str(activa or "").strip()

    if activa_normalizada in {"0", "1"}:
        return int(activa_normalizada)

    raise ValueError("El estado activo de la moneda es invalido.")


def _validar_orden(orden: Any) -> int:
    try:
        orden_validado = int(str(orden or "0").strip())
    except ValueError as exc:
        raise ValueError("El orden de la moneda debe ser numerico.") from exc

    if orden_validado < 0:
        raise ValueError("El orden de la moneda no puede ser negativo.")

    return orden_validado
