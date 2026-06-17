import json
import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db
from app.shared.transacciones_repository import contexto_escritura

_TIPOS_MOVIMIENTO_VALIDOS = {"INGRESO", "EGRESO"}
_ESTADOS_VALIDOS = {"PENDIENTE", "CONFIRMADA", "ANULADA"}

_COLUMNAS_SELECT = """
    id,
    origen_tipo,
    origen_payload_json,
    tipo_movimiento,
    total_esperado_centavos,
    estado,
    resultado_tipo,
    resultado_id,
    observaciones,
    creado_en,
    confirmado_en,
    anulado_en
"""


def crear_intencion_caja(datos: dict[str, Any]) -> dict[str, Any]:
    datos_validados = _validar_datos_creacion(datos)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with contexto_escritura(db):
            cursor = db.execute(
                """
                INSERT INTO caja_intenciones (
                    origen_tipo,
                    origen_payload_json,
                    tipo_movimiento,
                    total_esperado_centavos,
                    estado,
                    observaciones,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos_validados["origen_tipo"],
                    datos_validados["origen_payload_json"],
                    datos_validados["tipo_movimiento"],
                    datos_validados["total_esperado_centavos"],
                    "PENDIENTE",
                    datos_validados["observaciones"],
                    creado_en,
                ),
            )
            intencion_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo crear la intencion de caja.") from exc

    intencion = obtener_intencion_caja_por_id(intencion_id)
    if intencion is None:
        raise ValueError("No se pudo recuperar la intencion de caja creada.")

    return intencion


def obtener_intencion_caja_por_id(intencion_id: Any) -> dict[str, Any] | None:
    intencion_id_validado = _validar_entero_positivo(
        intencion_id,
        "La intencion de caja es obligatoria.",
    )

    fila = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT}
        FROM caja_intenciones
        WHERE id = ?
        LIMIT 1
        """,
        (intencion_id_validado,),
    ).fetchone()

    if fila is None:
        return None

    return _normalizar_fila(fila)


def marcar_intencion_caja_confirmada(
    intencion_id: Any,
    *,
    resultado_tipo: Any,
    resultado_id: Any,
) -> dict[str, Any]:
    intencion_id_validado = _validar_entero_positivo(
        intencion_id,
        "La intencion de caja es obligatoria.",
    )
    resultado_tipo_validado = _validar_texto_obligatorio(
        resultado_tipo,
        "El tipo de resultado es obligatorio.",
    ).upper()
    resultado_id_validado = _validar_entero_positivo(
        resultado_id,
        "El id de resultado es obligatorio.",
    )
    confirmado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with contexto_escritura(db):
            cursor = db.execute(
                """
                UPDATE caja_intenciones
                SET estado = ?,
                    resultado_tipo = ?,
                    resultado_id = ?,
                    confirmado_en = ?
                WHERE id = ?
                  AND estado = ?
                """,
                (
                    "CONFIRMADA",
                    resultado_tipo_validado,
                    resultado_id_validado,
                    confirmado_en,
                    intencion_id_validado,
                    "PENDIENTE",
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo confirmar la intencion de caja.") from exc

    if cursor.rowcount != 1:
        raise ValueError("La intencion de caja no esta pendiente o no existe.")

    intencion = obtener_intencion_caja_por_id(intencion_id_validado)
    if intencion is None:
        raise ValueError("No se pudo recuperar la intencion de caja confirmada.")

    return intencion


def _validar_datos_creacion(datos: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(datos, dict):
        raise ValueError("Los datos de intencion de caja son obligatorios.")

    origen_tipo = _validar_texto_obligatorio(
        datos.get("origen_tipo"),
        "El origen de la intencion de caja es obligatorio.",
    ).upper()
    tipo_movimiento = _validar_opcion(
        datos.get("tipo_movimiento"),
        _TIPOS_MOVIMIENTO_VALIDOS,
        "El tipo de movimiento de la intencion de caja es invalido.",
    )
    total_esperado_centavos = _validar_entero_positivo(
        datos.get("total_esperado_centavos"),
        "El total esperado de caja debe ser mayor a cero.",
    )
    payload = datos.get("origen_payload")
    if not isinstance(payload, dict):
        raise ValueError("El payload de origen de caja es obligatorio.")

    payload_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    observaciones = _normalizar_texto_opcional(datos.get("observaciones"))

    return {
        "origen_tipo": origen_tipo,
        "origen_payload_json": payload_json,
        "tipo_movimiento": tipo_movimiento,
        "total_esperado_centavos": total_esperado_centavos,
        "observaciones": observaciones,
    }


def _normalizar_fila(fila: Any) -> dict[str, Any]:
    intencion = dict(fila)
    intencion["id"] = int(intencion["id"])
    intencion["total_esperado_centavos"] = int(intencion["total_esperado_centavos"])
    intencion["esta_pendiente"] = intencion["estado"] == "PENDIENTE"
    intencion["esta_confirmada"] = intencion["estado"] == "CONFIRMADA"
    intencion["esta_anulada"] = intencion["estado"] == "ANULADA"

    if intencion.get("resultado_id") is not None:
        intencion["resultado_id"] = int(intencion["resultado_id"])

    try:
        intencion["origen_payload"] = json.loads(intencion["origen_payload_json"])
    except json.JSONDecodeError as exc:
        raise ValueError("El payload de la intencion de caja no es JSON valido.") from exc

    return intencion


def _validar_texto_obligatorio(valor: Any, mensaje: str) -> str:
    texto = str(valor or "").strip()
    if not texto:
        raise ValueError(mensaje)

    return texto


def _normalizar_texto_opcional(valor: Any) -> str | None:
    texto = str(valor or "").strip()
    return texto or None


def _validar_entero_positivo(valor: Any, mensaje: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje)

    try:
        entero = int(str(valor or "").strip())
    except ValueError as exc:
        raise ValueError(mensaje) from exc

    if entero <= 0:
        raise ValueError(mensaje)

    return entero


def _validar_opcion(valor: Any, opciones: set[str], mensaje: str) -> str:
    texto = str(valor or "").strip().upper()

    if texto not in opciones:
        raise ValueError(mensaje)

    return texto
