import re
import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db
from app.shared.transacciones_repository import contexto_escritura

_TIPOS_MOVIMIENTO_VALIDOS = {"INGRESO", "EGRESO"}
_ESTADOS_MOVIMIENTO_VALIDOS = {"BORRADOR", "CONFIRMADO", "ANULADO"}
_PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PATRON_MONEDA = re.compile(r"^[A-Z]{3}$")

_COLUMNAS_SELECT_MOVIMIENTOS_CAJA = """
    movimientos_caja.id,
    movimientos_caja.fecha,
    movimientos_caja.tipo_movimiento,
    movimientos_caja.origen_tipo,
    movimientos_caja.origen_id,
    movimientos_caja.moneda_contable_codigo,
    movimientos_caja.total_contable_centavos,
    movimientos_caja.estado,
    movimientos_caja.asiento_id,
    movimientos_caja.observaciones,
    movimientos_caja.creado_en,
    movimientos_caja.actualizado_en,
    movimientos_caja.confirmado_en,
    movimientos_caja.anulado_en,
    monedas.nombre AS moneda_contable_nombre,
    monedas.simbolo AS moneda_contable_simbolo
"""

_COLUMNAS_SELECT_MOVIMIENTOS_CAJA_LINEAS = """
    movimientos_caja_lineas.id,
    movimientos_caja_lineas.movimiento_caja_id,
    movimientos_caja_lineas.medio_operativo_codigo,
    movimientos_caja_lineas.cuenta_contable_codigo,
    movimientos_caja_lineas.moneda_codigo,
    movimientos_caja_lineas.fecha_valor,
    movimientos_caja_lineas.referencia,
    movimientos_caja_lineas.importe_nominal_centavos,
    movimientos_caja_lineas.cotizacion_1000000,
    movimientos_caja_lineas.importe_contable_centavos,
    movimientos_caja_lineas.detalle,
    movimientos_caja_lineas.orden,
    medios_operativos.nombre AS medio_operativo_nombre,
    medios_operativos.tipo AS medio_operativo_tipo,
    cuentas_contables.descripcion AS cuenta_contable_descripcion,
    monedas.nombre AS moneda_nombre,
    monedas.simbolo AS moneda_simbolo
"""


def crear_movimiento_caja(
    datos_movimiento: dict[str, Any],
    lineas_movimiento: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Inserta un movimiento de caja con sus lineas.

    Repository: persiste cabecera y snapshots de lineas. No resuelve medio
    operativo ni genera asiento; eso pertenece al service.
    """
    datos_validados = _validar_datos_movimiento(datos_movimiento)
    lineas_validadas = _validar_lineas_movimiento(lineas_movimiento)
    _validar_total_lineas(
        datos_validados["total_contable_centavos"],
        lineas_validadas,
    )

    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    confirmado_en = creado_en if datos_validados["estado"] == "CONFIRMADO" else None
    anulado_en = creado_en if datos_validados["estado"] == "ANULADO" else None

    db = get_db()

    try:
        with contexto_escritura(db):
            cursor = db.execute(
                """
                INSERT INTO movimientos_caja (
                    fecha,
                    tipo_movimiento,
                    origen_tipo,
                    origen_id,
                    moneda_contable_codigo,
                    total_contable_centavos,
                    estado,
                    asiento_id,
                    observaciones,
                    creado_en,
                    confirmado_en,
                    anulado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos_validados["fecha"],
                    datos_validados["tipo_movimiento"],
                    datos_validados["origen_tipo"],
                    datos_validados["origen_id"],
                    datos_validados["moneda_contable_codigo"],
                    datos_validados["total_contable_centavos"],
                    datos_validados["estado"],
                    datos_validados["asiento_id"],
                    datos_validados["observaciones"],
                    creado_en,
                    confirmado_en,
                    anulado_en,
                ),
            )
            movimiento_id = int(cursor.lastrowid)

            for indice, linea in enumerate(lineas_validadas, start=1):
                db.execute(
                    """
                    INSERT INTO movimientos_caja_lineas (
                        movimiento_caja_id,
                        medio_operativo_codigo,
                        cuenta_contable_codigo,
                        moneda_codigo,
                        fecha_valor,
                        referencia,
                        importe_nominal_centavos,
                        cotizacion_1000000,
                        importe_contable_centavos,
                        detalle,
                        orden
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        movimiento_id,
                        linea["medio_operativo_codigo"],
                        linea["cuenta_contable_codigo"],
                        linea["moneda_codigo"],
                        linea["fecha_valor"],
                        linea["referencia"],
                        linea["importe_nominal_centavos"],
                        linea["cotizacion_1000000"],
                        linea["importe_contable_centavos"],
                        linea["detalle"],
                        linea["orden"] or indice,
                    ),
                )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear el movimiento de caja. Revise medio operativo, "
            "cuenta, moneda, asiento, origen o duplicados funcionales."
        ) from exc

    movimiento = obtener_movimiento_caja_por_id(movimiento_id)

    if movimiento is None:
        raise ValueError("No se pudo recuperar el movimiento de caja creado.")

    return movimiento


def obtener_movimiento_caja_por_id(movimiento_id: Any) -> dict[str, Any] | None:
    movimiento_id_validado = _validar_entero_positivo(
        movimiento_id,
        "El id del movimiento de caja es obligatorio.",
    )

    fila = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MOVIMIENTOS_CAJA}
        FROM movimientos_caja
        JOIN monedas
          ON monedas.codigo = movimientos_caja.moneda_contable_codigo
        WHERE movimientos_caja.id = ?
        LIMIT 1
        """,
        (movimiento_id_validado,),
    ).fetchone()

    if fila is None:
        return None

    movimiento = _normalizar_fila_movimiento(fila)
    movimiento["lineas"] = listar_lineas_movimiento_caja(movimiento["id"])

    return movimiento


def listar_lineas_movimiento_caja(movimiento_id: Any) -> list[dict[str, Any]]:
    movimiento_id_validado = _validar_entero_positivo(
        movimiento_id,
        "El id del movimiento de caja es obligatorio.",
    )

    filas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MOVIMIENTOS_CAJA_LINEAS}
        FROM movimientos_caja_lineas
        JOIN medios_operativos
          ON medios_operativos.codigo = movimientos_caja_lineas.medio_operativo_codigo
        JOIN cuentas_contables
          ON cuentas_contables.cuenta = movimientos_caja_lineas.cuenta_contable_codigo
        JOIN monedas
          ON monedas.codigo = movimientos_caja_lineas.moneda_codigo
        WHERE movimientos_caja_lineas.movimiento_caja_id = ?
        ORDER BY movimientos_caja_lineas.orden, movimientos_caja_lineas.id
        """,
        (movimiento_id_validado,),
    ).fetchall()

    return [_normalizar_fila_linea(fila) for fila in filas]


def listar_movimientos_caja(limite: int = 100) -> list[dict[str, Any]]:
    limite_validado = _validar_limite(limite)

    filas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MOVIMIENTOS_CAJA}
        FROM movimientos_caja
        JOIN monedas
          ON monedas.codigo = movimientos_caja.moneda_contable_codigo
        ORDER BY movimientos_caja.fecha DESC, movimientos_caja.id DESC
        LIMIT ?
        """,
        (limite_validado,),
    ).fetchall()

    return [_normalizar_fila_movimiento(fila) for fila in filas]


def _normalizar_fila_movimiento(fila) -> dict[str, Any]:
    movimiento = dict(fila)

    movimiento["id"] = int(movimiento["id"])
    movimiento["total_contable_centavos"] = int(movimiento["total_contable_centavos"])
    movimiento["esta_confirmado"] = movimiento["estado"] == "CONFIRMADO"
    movimiento["esta_anulado"] = movimiento["estado"] == "ANULADO"

    if movimiento.get("origen_id") is not None:
        movimiento["origen_id"] = int(movimiento["origen_id"])

    if movimiento.get("asiento_id") is not None:
        movimiento["asiento_id"] = int(movimiento["asiento_id"])

    return movimiento


def _normalizar_fila_linea(fila) -> dict[str, Any]:
    linea = dict(fila)

    for campo in (
        "id",
        "movimiento_caja_id",
        "importe_nominal_centavos",
        "cotizacion_1000000",
        "importe_contable_centavos",
        "orden",
    ):
        linea[campo] = int(linea[campo])

    return linea


def _validar_datos_movimiento(datos: dict[str, Any]) -> dict[str, Any]:
    fecha = _validar_fecha_iso(datos.get("fecha"), "La fecha del movimiento es obligatoria.")
    tipo_movimiento = _validar_opcion(
        datos.get("tipo_movimiento"),
        _TIPOS_MOVIMIENTO_VALIDOS,
        "El tipo de movimiento de caja es invalido.",
    )
    origen_tipo = _normalizar_texto_opcional(datos.get("origen_tipo"))

    if origen_tipo is not None:
        origen_tipo = origen_tipo.upper()

    origen_id = _validar_entero_positivo_opcional(datos.get("origen_id"))
    moneda_contable_codigo = _validar_codigo_moneda(
        datos.get("moneda_contable_codigo", "ARS"),
        "La moneda contable del movimiento es obligatoria.",
    )
    total_contable_centavos = _validar_entero_no_negativo(
        datos.get("total_contable_centavos", 0),
        "El total contable debe ser un entero no negativo.",
    )
    estado = _validar_opcion(
        datos.get("estado", "BORRADOR"),
        _ESTADOS_MOVIMIENTO_VALIDOS,
        "El estado del movimiento de caja es invalido.",
    )
    asiento_id = _validar_entero_positivo_opcional(datos.get("asiento_id"))
    observaciones = _normalizar_texto_opcional(datos.get("observaciones"))

    if (origen_tipo is None and origen_id is not None) or (
        origen_tipo is not None and origen_id is None
    ):
        raise ValueError("El origen del movimiento de caja debe informarse completo.")

    if total_contable_centavos <= 0:
        raise ValueError("El total contable del movimiento de caja debe ser mayor a cero.")

    return {
        "fecha": fecha,
        "tipo_movimiento": tipo_movimiento,
        "origen_tipo": origen_tipo,
        "origen_id": origen_id,
        "moneda_contable_codigo": moneda_contable_codigo,
        "total_contable_centavos": total_contable_centavos,
        "estado": estado,
        "asiento_id": asiento_id,
        "observaciones": observaciones,
    }


def _validar_lineas_movimiento(lineas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not lineas:
        raise ValueError("El movimiento de caja debe tener al menos una linea.")

    return [_validar_linea_movimiento(linea) for linea in lineas]


def _validar_linea_movimiento(linea: dict[str, Any]) -> dict[str, Any]:
    medio_operativo_codigo = _validar_texto_obligatorio(
        linea.get("medio_operativo_codigo"),
        "El medio operativo es obligatorio.",
    ).upper()
    cuenta_contable_codigo = _validar_texto_obligatorio(
        linea.get("cuenta_contable_codigo"),
        "La cuenta contable de la linea es obligatoria.",
    )
    moneda_codigo = _validar_codigo_moneda(
        linea.get("moneda_codigo"),
        "La moneda de la linea es obligatoria.",
    )
    fecha_valor = _validar_fecha_iso_opcional(linea.get("fecha_valor"))
    referencia = _normalizar_texto_opcional(linea.get("referencia"))
    importe_nominal_centavos = _validar_entero_positivo(
        linea.get("importe_nominal_centavos"),
        "El importe nominal de la linea debe ser mayor a cero.",
    )
    cotizacion_1000000 = _validar_entero_positivo(
        linea.get("cotizacion_1000000", 1_000_000),
        "La cotizacion de la linea debe ser mayor a cero.",
    )
    importe_contable_centavos = _validar_entero_positivo(
        linea.get("importe_contable_centavos"),
        "El importe contable de la linea debe ser mayor a cero.",
    )
    detalle = _normalizar_texto_opcional(linea.get("detalle"))
    orden = _validar_entero_no_negativo(
        linea.get("orden", 0),
        "El orden de la linea debe ser no negativo.",
    )

    return {
        "medio_operativo_codigo": medio_operativo_codigo,
        "cuenta_contable_codigo": cuenta_contable_codigo,
        "moneda_codigo": moneda_codigo,
        "fecha_valor": fecha_valor,
        "referencia": referencia,
        "importe_nominal_centavos": importe_nominal_centavos,
        "cotizacion_1000000": cotizacion_1000000,
        "importe_contable_centavos": importe_contable_centavos,
        "detalle": detalle,
        "orden": orden,
    }


def _validar_total_lineas(
    total_contable_centavos: int,
    lineas: list[dict[str, Any]],
) -> None:
    total_lineas = sum(linea["importe_contable_centavos"] for linea in lineas)

    if total_lineas != total_contable_centavos:
        raise ValueError("El total de lineas no coincide con el total de caja.")


def _validar_limite(limite: Any) -> int:
    limite_validado = _validar_entero_positivo(limite, "El limite debe ser positivo.")
    return min(limite_validado, 500)


def _validar_texto_obligatorio(valor: Any, mensaje: str) -> str:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        raise ValueError(mensaje)

    return valor_normalizado


def _normalizar_texto_opcional(valor: Any) -> str | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return valor_normalizado


def _validar_entero_positivo(valor: Any, mensaje: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje)

    try:
        valor_entero = int(str(valor).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(mensaje) from exc

    if valor_entero <= 0:
        raise ValueError(mensaje)

    return valor_entero


def _validar_entero_positivo_opcional(valor: Any) -> int | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return _validar_entero_positivo(
        valor_normalizado,
        "El id opcional informado debe ser positivo.",
    )


def _validar_entero_no_negativo(valor: Any, mensaje: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje)

    try:
        valor_entero = int(str(valor).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(mensaje) from exc

    if valor_entero < 0:
        raise ValueError(mensaje)

    return valor_entero


def _validar_opcion(valor: Any, opciones_validas: set[str], mensaje: str) -> str:
    valor_normalizado = str(valor or "").strip().upper()

    if valor_normalizado not in opciones_validas:
        raise ValueError(mensaje)

    return valor_normalizado


def _validar_codigo_moneda(valor: Any, mensaje: str) -> str:
    valor_normalizado = str(valor or "").strip().upper()

    if not _PATRON_MONEDA.match(valor_normalizado):
        raise ValueError(mensaje)

    return valor_normalizado


def _validar_fecha_iso(valor: Any, mensaje: str) -> str:
    valor_normalizado = str(valor or "").strip()

    if not _PATRON_FECHA_ISO.match(valor_normalizado):
        raise ValueError(mensaje)

    return valor_normalizado


def _validar_fecha_iso_opcional(valor: Any) -> str | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return _validar_fecha_iso(valor_normalizado, "La fecha valor debe ser ISO.")
