import re
import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db
from app.shared.transacciones_repository import contexto_escritura

_COLUMNAS_SELECT_CLIENTES_CTACTE_MOVIMIENTOS = """
    clientes_cuenta_corriente_movimientos.id,
    clientes_cuenta_corriente_movimientos.cliente_id,
    clientes_cuenta_corriente_movimientos.fecha,
    clientes_cuenta_corriente_movimientos.tipo_movimiento,
    clientes_cuenta_corriente_movimientos.descripcion,
    clientes_cuenta_corriente_movimientos.moneda_codigo,
    clientes_cuenta_corriente_movimientos.debe_centavos,
    clientes_cuenta_corriente_movimientos.haber_centavos,
    clientes_cuenta_corriente_movimientos.estado,
    clientes_cuenta_corriente_movimientos.origen_tipo,
    clientes_cuenta_corriente_movimientos.origen_id,
    clientes_cuenta_corriente_movimientos.asiento_id,
    clientes_cuenta_corriente_movimientos.creado_en,
    clientes_cuenta_corriente_movimientos.actualizado_en,
    clientes_cuenta_corriente_movimientos.confirmado_en,
    clientes_cuenta_corriente_movimientos.anulado_en,
    clientes.razon_social AS cliente_razon_social,
    monedas.nombre AS moneda_nombre,
    monedas.simbolo AS moneda_simbolo,
    monedas.decimales AS moneda_decimales
"""

_TIPOS_MOVIMIENTO_VALIDOS = {
    "FACTURA",
    "NOTA_DEBITO",
    "NOTA_CREDITO",
    "COBRANZA",
    "ANTICIPO",
    "AJUSTE",
}
_ESTADOS_MOVIMIENTO_VALIDOS = {"BORRADOR", "CONFIRMADO", "ANULADO"}
_PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PATRON_MONEDA = re.compile(r"^[A-Z]{3}$")


def crear_movimiento_cliente_cuenta_corriente(
    datos_movimiento: dict[str, Any],
) -> dict[str, Any]:
    """
    Inserta un movimiento DEBE/HABER de cuenta corriente de clientes.

    El repository persiste movimientos atomicos. No calcula ni persiste saldos.
    """
    datos_validados = _validar_datos_movimiento(datos_movimiento)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    confirmado_en = None
    anulado_en = None

    if datos_validados["estado"] == "CONFIRMADO":
        confirmado_en = creado_en
    elif datos_validados["estado"] == "ANULADO":
        anulado_en = creado_en

    db = get_db()

    try:
        with contexto_escritura(db):
            cursor = db.execute(
                """
                INSERT INTO clientes_cuenta_corriente_movimientos (
                    cliente_id,
                    fecha,
                    tipo_movimiento,
                    descripcion,
                    moneda_codigo,
                    debe_centavos,
                    haber_centavos,
                    estado,
                    origen_tipo,
                    origen_id,
                    asiento_id,
                    creado_en,
                    confirmado_en,
                    anulado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos_validados["cliente_id"],
                    datos_validados["fecha"],
                    datos_validados["tipo_movimiento"],
                    datos_validados["descripcion"],
                    datos_validados["moneda_codigo"],
                    datos_validados["debe_centavos"],
                    datos_validados["haber_centavos"],
                    datos_validados["estado"],
                    datos_validados["origen_tipo"],
                    datos_validados["origen_id"],
                    datos_validados["asiento_id"],
                    creado_en,
                    confirmado_en,
                    anulado_en,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear el movimiento de cuenta corriente del cliente. "
            "Revise cliente, moneda, asiento u origen informado."
        ) from exc

    movimiento = obtener_movimiento_cliente_cuenta_corriente_por_id(cursor.lastrowid)

    if movimiento is None:
        raise ValueError(
            "No se pudo recuperar el movimiento de cuenta corriente creado."
        )

    return movimiento


def obtener_movimiento_cliente_cuenta_corriente_por_id(
    movimiento_id: Any,
) -> dict[str, Any] | None:
    """Devuelve un movimiento de cuenta corriente de cliente por id."""
    movimiento_id_validado = _validar_entero_positivo(
        movimiento_id,
        "El id del movimiento es obligatorio.",
    )

    fila_movimiento = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CLIENTES_CTACTE_MOVIMIENTOS}
        FROM clientes_cuenta_corriente_movimientos
        JOIN clientes
          ON clientes.id = clientes_cuenta_corriente_movimientos.cliente_id
        JOIN monedas
          ON monedas.codigo = clientes_cuenta_corriente_movimientos.moneda_codigo
        WHERE clientes_cuenta_corriente_movimientos.id = ?
        LIMIT 1
        """,
        (movimiento_id_validado,),
    ).fetchone()

    if fila_movimiento is None:
        return None

    return _normalizar_fila_movimiento(fila_movimiento)


def listar_movimientos_cliente_cuenta_corriente(
    cliente_id: Any,
    estado: Any = None,
) -> list[dict[str, Any]]:
    """
    Lista movimientos de cuenta corriente de un cliente.

    Si estado es None, lista todos los estados. Si se informa estado, filtra por
    BORRADOR, CONFIRMADO o ANULADO.
    """
    cliente_id_validado = _validar_entero_positivo(
        cliente_id,
        "El cliente es obligatorio.",
    )
    estado_validado = None

    parametros: list[Any] = [cliente_id_validado]
    filtro_estado = ""

    if estado is not None:
        estado_validado = _validar_opcion(
            estado,
            _ESTADOS_MOVIMIENTO_VALIDOS,
            "El estado del movimiento es invalido.",
        )
        filtro_estado = (
            "AND clientes_cuenta_corriente_movimientos.estado = ?"
        )
        parametros.append(estado_validado)

    filas_movimientos = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CLIENTES_CTACTE_MOVIMIENTOS}
        FROM clientes_cuenta_corriente_movimientos
        JOIN clientes
          ON clientes.id = clientes_cuenta_corriente_movimientos.cliente_id
        JOIN monedas
          ON monedas.codigo = clientes_cuenta_corriente_movimientos.moneda_codigo
        WHERE clientes_cuenta_corriente_movimientos.cliente_id = ?
        {filtro_estado}
        ORDER BY clientes_cuenta_corriente_movimientos.fecha,
                 clientes_cuenta_corriente_movimientos.id
        """,
        tuple(parametros),
    ).fetchall()

    return [
        _normalizar_fila_movimiento(fila_movimiento)
        for fila_movimiento in filas_movimientos
    ]


def calcular_saldo_cliente_cuenta_corriente(
    cliente_id: Any,
    solo_confirmados: bool = True,
) -> dict[str, int]:
    """
    Calcula totales DEBE/HABER de la cuenta corriente de un cliente.

    No persiste el saldo: devuelve una lectura calculada desde movimientos.
    """
    cliente_id_validado = _validar_entero_positivo(
        cliente_id,
        "El cliente es obligatorio.",
    )

    filtro_estado = ""
    parametros: list[Any] = [cliente_id_validado]

    if solo_confirmados:
        filtro_estado = "AND estado = ?"
        parametros.append("CONFIRMADO")

    fila_saldo = get_db().execute(
        f"""
        SELECT
            COALESCE(SUM(debe_centavos), 0) AS total_debe_centavos,
            COALESCE(SUM(haber_centavos), 0) AS total_haber_centavos
        FROM clientes_cuenta_corriente_movimientos
        WHERE cliente_id = ?
        {filtro_estado}
        """,
        tuple(parametros),
    ).fetchone()

    total_debe_centavos = int(fila_saldo["total_debe_centavos"])
    total_haber_centavos = int(fila_saldo["total_haber_centavos"])

    return {
        "cliente_id": cliente_id_validado,
        "total_debe_centavos": total_debe_centavos,
        "total_haber_centavos": total_haber_centavos,
        "saldo_centavos": total_debe_centavos - total_haber_centavos,
    }


def _normalizar_fila_movimiento(fila_movimiento) -> dict[str, Any]:
    """Convierte una fila SQLite de cuenta corriente en dict explicito."""
    movimiento = dict(fila_movimiento)

    movimiento["id"] = int(movimiento["id"])
    movimiento["cliente_id"] = int(movimiento["cliente_id"])
    movimiento["debe_centavos"] = int(movimiento["debe_centavos"])
    movimiento["haber_centavos"] = int(movimiento["haber_centavos"])

    if movimiento.get("origen_id") is not None:
        movimiento["origen_id"] = int(movimiento["origen_id"])

    if movimiento.get("asiento_id") is not None:
        movimiento["asiento_id"] = int(movimiento["asiento_id"])

    if movimiento.get("moneda_decimales") is not None:
        movimiento["moneda_decimales"] = int(movimiento["moneda_decimales"])

    movimiento["lado"] = (
        "DEBE" if movimiento["debe_centavos"] > 0 else "HABER"
    )
    movimiento["importe_centavos"] = (
        movimiento["debe_centavos"]
        if movimiento["debe_centavos"] > 0
        else movimiento["haber_centavos"]
    )
    movimiento["esta_confirmado"] = movimiento["estado"] == "CONFIRMADO"
    movimiento["esta_anulado"] = movimiento["estado"] == "ANULADO"

    return movimiento


def _validar_datos_movimiento(datos_movimiento: dict[str, Any]) -> dict[str, Any]:
    cliente_id = _validar_entero_positivo(
        datos_movimiento.get("cliente_id"),
        "El cliente es obligatorio.",
    )
    fecha = _validar_fecha_iso(
        datos_movimiento.get("fecha"),
        "La fecha del movimiento es obligatoria.",
    )
    tipo_movimiento = _validar_opcion(
        datos_movimiento.get("tipo_movimiento"),
        _TIPOS_MOVIMIENTO_VALIDOS,
        "El tipo de movimiento es invalido.",
    )
    descripcion = _validar_texto_obligatorio(
        datos_movimiento.get("descripcion"),
        "La descripcion del movimiento es obligatoria.",
    )
    moneda_codigo = _validar_codigo_moneda(
        datos_movimiento.get("moneda_codigo", "ARS"),
        "La moneda del movimiento es obligatoria.",
    )
    debe_centavos = _validar_entero_no_negativo(
        datos_movimiento.get("debe_centavos", 0),
        "El importe DEBE debe ser un entero no negativo.",
    )
    haber_centavos = _validar_entero_no_negativo(
        datos_movimiento.get("haber_centavos", 0),
        "El importe HABER debe ser un entero no negativo.",
    )
    estado = _validar_opcion(
        datos_movimiento.get("estado", "BORRADOR"),
        _ESTADOS_MOVIMIENTO_VALIDOS,
        "El estado del movimiento es invalido.",
    )
    origen_tipo = _normalizar_texto_opcional(datos_movimiento.get("origen_tipo"))

    if origen_tipo is not None:
        origen_tipo = origen_tipo.upper()

    origen_id = _validar_entero_positivo_opcional(datos_movimiento.get("origen_id"))
    asiento_id = _validar_entero_positivo_opcional(datos_movimiento.get("asiento_id"))

    if (debe_centavos > 0 and haber_centavos > 0) or (
        debe_centavos == 0 and haber_centavos == 0
    ):
        raise ValueError("El movimiento debe tener importe en DEBE o HABER, no ambos.")

    if (origen_tipo is None and origen_id is not None) or (
        origen_tipo is not None and origen_id is None
    ):
        raise ValueError("El origen del movimiento debe informarse completo.")

    return {
        "cliente_id": cliente_id,
        "fecha": fecha,
        "tipo_movimiento": tipo_movimiento,
        "descripcion": descripcion,
        "moneda_codigo": moneda_codigo,
        "debe_centavos": debe_centavos,
        "haber_centavos": haber_centavos,
        "estado": estado,
        "origen_tipo": origen_tipo,
        "origen_id": origen_id,
        "asiento_id": asiento_id,
    }


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

    mes = int(valor_normalizado[5:7])
    dia = int(valor_normalizado[8:10])

    if mes < 1 or mes > 12 or dia < 1 or dia > 31:
        raise ValueError(mensaje)

    return valor_normalizado
