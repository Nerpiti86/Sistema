import re
import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db
from app.shared.transacciones_repository import contexto_escritura

_TIPOS_COBRANZA_VALIDOS = {"APLICADA", "ANTICIPO", "MIXTA"}
_TIPOS_LINEA_VALIDOS = {"FACTURA", "NOTA_DEBITO", "ANTICIPO"}
_ESTADOS_COBRANZA_VALIDOS = {"BORRADOR", "CONFIRMADO", "ANULADO"}
_PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PATRON_MONEDA = re.compile(r"^[A-Z]{3}$")

_COLUMNAS_SELECT_CLIENTES_COBRANZAS = """
    clientes_cobranzas.id,
    clientes_cobranzas.cliente_id,
    clientes_cobranzas.fecha,
    clientes_cobranzas.tipo_cobranza,
    clientes_cobranzas.tipo_comprobante,
    clientes_cobranzas.letra,
    clientes_cobranzas.punto_venta,
    clientes_cobranzas.numero,
    clientes_cobranzas.moneda_codigo,
    clientes_cobranzas.cotizacion_1000000,
    clientes_cobranzas.total_centavos,
    clientes_cobranzas.estado,
    clientes_cobranzas.asiento_id,
    clientes_cobranzas.observaciones,
    clientes_cobranzas.creado_en,
    clientes_cobranzas.actualizado_en,
    clientes_cobranzas.confirmado_en,
    clientes_cobranzas.anulado_en,
    clientes.razon_social AS cliente_razon_social,
    monedas.nombre AS moneda_nombre,
    monedas.simbolo AS moneda_simbolo
"""

_COLUMNAS_SELECT_CLIENTES_COBRANZAS_LINEAS = """
    clientes_cobranzas_lineas.id,
    clientes_cobranzas_lineas.cobranza_cliente_id,
    clientes_cobranzas_lineas.tipo_linea,
    clientes_cobranzas_lineas.movimiento_ctacte_cancelado_id,
    clientes_cobranzas_lineas.venta_comprobante_id,
    clientes_cobranzas_lineas.movimiento_ctacte_generado_id,
    clientes_cobranzas_lineas.importe_centavos,
    clientes_cobranzas_lineas.cuenta_cancelacion_codigo,
    clientes_cobranzas_lineas.orden,
    clientes_cobranzas_lineas.observaciones,
    cuentas_contables.descripcion AS cuenta_cancelacion_descripcion
"""


def crear_cobranza_cliente(
    datos_cobranza: dict[str, Any],
    lineas_cobranza: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Inserta una cobranza de cliente con lineas funcionales.

    Repository: persiste cabecera y lineas. No calcula saldos abiertos, no resuelve
    cuentas del cliente ni genera asiento/cuenta corriente; eso pertenece al service.
    """
    datos_validados = _validar_datos_cobranza(datos_cobranza)
    lineas_validadas = _validar_lineas_cobranza(lineas_cobranza)
    _validar_total_lineas(datos_validados["total_centavos"], lineas_validadas)

    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    confirmado_en = creado_en if datos_validados["estado"] == "CONFIRMADO" else None
    anulado_en = creado_en if datos_validados["estado"] == "ANULADO" else None

    db = get_db()

    try:
        with contexto_escritura(db):
            cursor = db.execute(
                """
                INSERT INTO clientes_cobranzas (
                    cliente_id,
                    fecha,
                    tipo_cobranza,
                    tipo_comprobante,
                    letra,
                    punto_venta,
                    numero,
                    moneda_codigo,
                    cotizacion_1000000,
                    total_centavos,
                    estado,
                    asiento_id,
                    observaciones,
                    creado_en,
                    confirmado_en,
                    anulado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos_validados["cliente_id"],
                    datos_validados["fecha"],
                    datos_validados["tipo_cobranza"],
                    datos_validados["tipo_comprobante"],
                    datos_validados["letra"],
                    datos_validados["punto_venta"],
                    datos_validados["numero"],
                    datos_validados["moneda_codigo"],
                    datos_validados["cotizacion_1000000"],
                    datos_validados["total_centavos"],
                    datos_validados["estado"],
                    datos_validados["asiento_id"],
                    datos_validados["observaciones"],
                    creado_en,
                    confirmado_en,
                    anulado_en,
                ),
            )
            cobranza_id = int(cursor.lastrowid)

            for indice, linea in enumerate(lineas_validadas, start=1):
                db.execute(
                    """
                    INSERT INTO clientes_cobranzas_lineas (
                        cobranza_cliente_id,
                        tipo_linea,
                        movimiento_ctacte_cancelado_id,
                        venta_comprobante_id,
                        movimiento_ctacte_generado_id,
                        importe_centavos,
                        cuenta_cancelacion_codigo,
                        orden,
                        observaciones
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cobranza_id,
                        linea["tipo_linea"],
                        linea["movimiento_ctacte_cancelado_id"],
                        linea["venta_comprobante_id"],
                        linea["movimiento_ctacte_generado_id"],
                        linea["importe_centavos"],
                        linea["cuenta_cancelacion_codigo"],
                        linea["orden"] or indice,
                        linea["observaciones"],
                    ),
                )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear la cobranza del cliente. Revise cliente, moneda, "
            "cuentas, comprobantes, movimientos o duplicados funcionales."
        ) from exc

    cobranza = obtener_cobranza_cliente_por_id(cobranza_id)

    if cobranza is None:
        raise ValueError("No se pudo recuperar la cobranza creada.")

    return cobranza


def obtener_cobranza_cliente_por_id(cobranza_id: Any) -> dict[str, Any] | None:
    cobranza_id_validada = _validar_entero_positivo(
        cobranza_id,
        "El id de la cobranza es obligatorio.",
    )

    fila = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CLIENTES_COBRANZAS}
        FROM clientes_cobranzas
        JOIN clientes
          ON clientes.id = clientes_cobranzas.cliente_id
        JOIN monedas
          ON monedas.codigo = clientes_cobranzas.moneda_codigo
        WHERE clientes_cobranzas.id = ?
        LIMIT 1
        """,
        (cobranza_id_validada,),
    ).fetchone()

    if fila is None:
        return None

    cobranza = _normalizar_fila_cobranza(fila)
    cobranza["lineas"] = listar_lineas_cobranza_cliente(cobranza["id"])

    return cobranza


def listar_lineas_cobranza_cliente(cobranza_id: Any) -> list[dict[str, Any]]:
    cobranza_id_validada = _validar_entero_positivo(
        cobranza_id,
        "El id de la cobranza es obligatorio.",
    )

    filas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CLIENTES_COBRANZAS_LINEAS}
        FROM clientes_cobranzas_lineas
        JOIN cuentas_contables
          ON cuentas_contables.cuenta = clientes_cobranzas_lineas.cuenta_cancelacion_codigo
        WHERE clientes_cobranzas_lineas.cobranza_cliente_id = ?
        ORDER BY clientes_cobranzas_lineas.orden, clientes_cobranzas_lineas.id
        """,
        (cobranza_id_validada,),
    ).fetchall()

    return [_normalizar_fila_linea(fila) for fila in filas]


def listar_cobranzas_cliente(
    cliente_id: Any,
    limite: int = 100,
) -> list[dict[str, Any]]:
    cliente_id_validado = _validar_entero_positivo(
        cliente_id,
        "El cliente es obligatorio.",
    )
    limite_validado = _validar_limite(limite)

    filas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CLIENTES_COBRANZAS}
        FROM clientes_cobranzas
        JOIN clientes
          ON clientes.id = clientes_cobranzas.cliente_id
        JOIN monedas
          ON monedas.codigo = clientes_cobranzas.moneda_codigo
        WHERE clientes_cobranzas.cliente_id = ?
        ORDER BY clientes_cobranzas.fecha DESC, clientes_cobranzas.id DESC
        LIMIT ?
        """,
        (cliente_id_validado, limite_validado),
    ).fetchall()

    return [_normalizar_fila_cobranza(fila) for fila in filas]


def _normalizar_fila_cobranza(fila) -> dict[str, Any]:
    cobranza = dict(fila)

    for campo in (
        "id",
        "cliente_id",
        "punto_venta",
        "numero",
        "cotizacion_1000000",
        "total_centavos",
    ):
        cobranza[campo] = int(cobranza[campo])

    if cobranza.get("asiento_id") is not None:
        cobranza["asiento_id"] = int(cobranza["asiento_id"])

    cobranza["esta_confirmada"] = cobranza["estado"] == "CONFIRMADO"
    cobranza["esta_anulada"] = cobranza["estado"] == "ANULADO"

    return cobranza


def _normalizar_fila_linea(fila) -> dict[str, Any]:
    linea = dict(fila)

    for campo in ("id", "cobranza_cliente_id", "importe_centavos", "orden"):
        linea[campo] = int(linea[campo])

    for campo in (
        "movimiento_ctacte_cancelado_id",
        "venta_comprobante_id",
        "movimiento_ctacte_generado_id",
    ):
        if linea.get(campo) is not None:
            linea[campo] = int(linea[campo])

    return linea


def _validar_datos_cobranza(datos: dict[str, Any]) -> dict[str, Any]:
    cliente_id = _validar_entero_positivo(
        datos.get("cliente_id"),
        "El cliente es obligatorio.",
    )
    fecha = _validar_fecha_iso(datos.get("fecha"), "La fecha de cobranza es obligatoria.")
    tipo_cobranza = _validar_opcion(
        datos.get("tipo_cobranza"),
        _TIPOS_COBRANZA_VALIDOS,
        "El tipo de cobranza es invalido.",
    )
    tipo_comprobante = _validar_opcion(
        datos.get("tipo_comprobante", "RECIBO"),
        {"RECIBO"},
        "El tipo de comprobante de cobranza es invalido.",
    )
    letra = _validar_texto_obligatorio(datos.get("letra", "C"), "La letra es obligatoria.").upper()
    punto_venta = _validar_entero_no_negativo(
        datos.get("punto_venta", 0),
        "El punto de venta debe ser no negativo.",
    )
    numero = _validar_entero_no_negativo(
        datos.get("numero", 0),
        "El numero debe ser no negativo.",
    )
    moneda_codigo = _validar_codigo_moneda(
        datos.get("moneda_codigo", "ARS"),
        "La moneda de cobranza es obligatoria.",
    )
    cotizacion_1000000 = _validar_entero_positivo(
        datos.get("cotizacion_1000000", 1_000_000),
        "La cotizacion de cobranza debe ser mayor a cero.",
    )
    total_centavos = _validar_entero_no_negativo(
        datos.get("total_centavos", 0),
        "El total de cobranza debe ser un entero no negativo.",
    )
    estado = _validar_opcion(
        datos.get("estado", "BORRADOR"),
        _ESTADOS_COBRANZA_VALIDOS,
        "El estado de la cobranza es invalido.",
    )
    asiento_id = _validar_entero_positivo_opcional(datos.get("asiento_id"))
    observaciones = _normalizar_texto_opcional(datos.get("observaciones"))

    if total_centavos <= 0:
        raise ValueError("El total de cobranza debe ser mayor a cero.")

    return {
        "cliente_id": cliente_id,
        "fecha": fecha,
        "tipo_cobranza": tipo_cobranza,
        "tipo_comprobante": tipo_comprobante,
        "letra": letra,
        "punto_venta": punto_venta,
        "numero": numero,
        "moneda_codigo": moneda_codigo,
        "cotizacion_1000000": cotizacion_1000000,
        "total_centavos": total_centavos,
        "estado": estado,
        "asiento_id": asiento_id,
        "observaciones": observaciones,
    }


def _validar_lineas_cobranza(lineas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not lineas:
        raise ValueError("La cobranza debe tener al menos una linea.")

    return [_validar_linea_cobranza(linea) for linea in lineas]


def _validar_linea_cobranza(linea: dict[str, Any]) -> dict[str, Any]:
    tipo_linea = _validar_opcion(
        linea.get("tipo_linea"),
        _TIPOS_LINEA_VALIDOS,
        "El tipo de linea de cobranza es invalido.",
    )
    movimiento_ctacte_cancelado_id = _validar_entero_positivo_opcional(
        linea.get("movimiento_ctacte_cancelado_id")
    )
    venta_comprobante_id = _validar_entero_positivo_opcional(
        linea.get("venta_comprobante_id")
    )
    movimiento_ctacte_generado_id = _validar_entero_positivo_opcional(
        linea.get("movimiento_ctacte_generado_id")
    )
    importe_centavos = _validar_entero_positivo(
        linea.get("importe_centavos"),
        "El importe de la linea debe ser mayor a cero.",
    )
    cuenta_cancelacion_codigo = _validar_texto_obligatorio(
        linea.get("cuenta_cancelacion_codigo"),
        "La cuenta de cancelacion es obligatoria.",
    )
    orden = _validar_entero_no_negativo(
        linea.get("orden", 0),
        "El orden de la linea debe ser no negativo.",
    )
    observaciones = _normalizar_texto_opcional(linea.get("observaciones"))

    if tipo_linea == "ANTICIPO":
        if movimiento_ctacte_cancelado_id is not None or venta_comprobante_id is not None:
            raise ValueError("La linea de anticipo no debe informar comprobante cancelado.")
    elif movimiento_ctacte_cancelado_id is None or venta_comprobante_id is None:
        raise ValueError("La linea aplicada debe informar movimiento y comprobante cancelado.")

    return {
        "tipo_linea": tipo_linea,
        "movimiento_ctacte_cancelado_id": movimiento_ctacte_cancelado_id,
        "venta_comprobante_id": venta_comprobante_id,
        "movimiento_ctacte_generado_id": movimiento_ctacte_generado_id,
        "importe_centavos": importe_centavos,
        "cuenta_cancelacion_codigo": cuenta_cancelacion_codigo,
        "orden": orden,
        "observaciones": observaciones,
    }


def _validar_total_lineas(total_centavos: int, lineas: list[dict[str, Any]]) -> None:
    total_lineas = sum(linea["importe_centavos"] for linea in lineas)

    if total_lineas != total_centavos:
        raise ValueError("El total de lineas no coincide con el total de cobranza.")


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
