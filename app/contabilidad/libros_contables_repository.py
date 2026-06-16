from datetime import datetime
from typing import Any

from app.db import get_db

_ESTADOS_ASIENTO_VALIDOS = {"BORRADOR", "CONFIRMADO", "ANULADO"}
_PATRON_FECHA_ISO = "%Y-%m-%d"


def listar_movimientos_libro_diario(
    ejercicio_id: Any,
    fecha_desde: Any = None,
    fecha_hasta: Any = None,
    estado: Any = "CONFIRMADO",
) -> list[dict[str, Any]]:
    """
    Devuelve renglones contables planos para armar el Libro Diario.

    El repository concentra SQL y devuelve filas normalizadas. La agrupacion,
    formateo y totales de pantalla pertenecen al service.
    """
    ejercicio_id_validado = _validar_entero_positivo(
        ejercicio_id,
        "El ejercicio contable es obligatorio.",
    )
    fecha_desde_validada = _validar_fecha_iso_opcional(
        fecha_desde,
        "La fecha desde debe tener formato YYYY-MM-DD.",
    )
    fecha_hasta_validada = _validar_fecha_iso_opcional(
        fecha_hasta,
        "La fecha hasta debe tener formato YYYY-MM-DD.",
    )

    if (
        fecha_desde_validada is not None
        and fecha_hasta_validada is not None
        and fecha_desde_validada > fecha_hasta_validada
    ):
        raise ValueError("La fecha desde no puede ser posterior a la fecha hasta.")

    estado_validado = _validar_estado_opcional(estado)

    condiciones = ["asientos_contables.ejercicio_id = ?"]
    parametros: list[Any] = [ejercicio_id_validado]

    if fecha_desde_validada is not None:
        condiciones.append("asientos_contables.fecha >= ?")
        parametros.append(fecha_desde_validada)

    if fecha_hasta_validada is not None:
        condiciones.append("asientos_contables.fecha <= ?")
        parametros.append(fecha_hasta_validada)

    if estado_validado is not None:
        condiciones.append("asientos_contables.estado = ?")
        parametros.append(estado_validado)

    where_sql = " AND ".join(condiciones)

    filas = get_db().execute(
        f"""
        SELECT
            asientos_contables.id AS asiento_id,
            asientos_contables.ejercicio_id,
            ejercicios_contables.codigo AS ejercicio_codigo,
            asientos_contables.numero_asiento,
            asientos_contables.fecha,
            asientos_contables.descripcion AS asiento_descripcion,
            asientos_contables.estado,
            asientos_contables.tipo,
            asientos_contables_detalle.id AS detalle_id,
            asientos_contables_detalle.renglon,
            asientos_contables_detalle.cuenta_contable_codigo,
            cuentas_contables.descripcion AS cuenta_nombre,
            asientos_contables_detalle.descripcion AS detalle_descripcion,
            asientos_contables_detalle.debe_centavos,
            asientos_contables_detalle.haber_centavos
        FROM asientos_contables
        JOIN ejercicios_contables
          ON ejercicios_contables.id = asientos_contables.ejercicio_id
        JOIN asientos_contables_detalle
          ON asientos_contables_detalle.asiento_id = asientos_contables.id
        JOIN cuentas_contables
          ON cuentas_contables.cuenta = asientos_contables_detalle.cuenta_contable_codigo
        WHERE {where_sql}
        ORDER BY
            asientos_contables.fecha,
            asientos_contables.numero_asiento,
            asientos_contables.id,
            asientos_contables_detalle.renglon
        """,
        parametros,
    ).fetchall()

    return [_normalizar_movimiento_libro_diario(fila) for fila in filas]


def _normalizar_movimiento_libro_diario(fila) -> dict[str, Any]:
    movimiento = dict(fila)

    for campo in (
        "asiento_id",
        "ejercicio_id",
        "detalle_id",
        "renglon",
        "debe_centavos",
        "haber_centavos",
    ):
        movimiento[campo] = int(movimiento[campo])

    if movimiento["numero_asiento"] is not None:
        movimiento["numero_asiento"] = int(movimiento["numero_asiento"])

    return movimiento


def _validar_entero_positivo(valor: Any, mensaje_error: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje_error)

    try:
        valor_entero = int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(mensaje_error) from exc

    if valor_entero <= 0:
        raise ValueError(mensaje_error)

    return valor_entero


def _validar_fecha_iso_opcional(valor: Any, mensaje_error: str) -> str | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    try:
        datetime.strptime(valor_normalizado, _PATRON_FECHA_ISO)
    except ValueError as exc:
        raise ValueError(mensaje_error) from exc

    return valor_normalizado


def _validar_estado_opcional(valor: Any) -> str | None:
    valor_normalizado = str(valor or "").strip().upper()

    if not valor_normalizado:
        return None

    if valor_normalizado not in _ESTADOS_ASIENTO_VALIDOS:
        raise ValueError("El estado del asiento es invalido.")

    return valor_normalizado
