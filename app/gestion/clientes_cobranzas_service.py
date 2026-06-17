from datetime import date
import re
from typing import Any

from app.caja.movimientos_caja_repository import crear_movimiento_caja
from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_automatico_confirmado,
)
from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_por_fecha,
)
from app.gestion.clientes_cobranzas_repository import (
    crear_cobranza_cliente,
    obtener_cobranza_cliente_por_id,
    vincular_linea_cobranza_movimiento_ctacte_generado,
)
from app.gestion.clientes_cuenta_corriente_repository import (
    obtener_movimiento_cliente_cuenta_corriente_por_id,
)
from app.gestion.clientes_cuenta_corriente_service import crear_movimiento_haber_cliente
from app.gestion.clientes_repository import obtener_cliente_por_id, validar_cliente_activo
from app.gestion.ventas_comprobantes_repository import obtener_venta_comprobante_por_id
from app.shared.medios_operativos_repository import obtener_medio_operativo_por_codigo
from app.shared.transacciones_repository import ejecutar_en_transaccion

_MONEDA_CONTABLE = "ARS"
_ESCALA_COTIZACION_CONTABLE = 1_000_000
_ORIGEN_CLIENTE_COBRANZA = "CLIENTE_COBRANZA"
_ORIGEN_VENTA_COMPROBANTE = "VENTA_COMPROBANTE"
_TIPO_ASIENTO_COBRANZA = "COBRANZA"
_TIPO_MOVIMIENTO_CAJA_INGRESO = "INGRESO"
_TIPO_COBRANZA_APLICADA = "APLICADA"
_TIPO_COMPROBANTE_RECIBO = "RECIBO"
_LETRA_RECIBO_DEFAULT = "C"
_PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def crear_cobranza_aplicada_confirmada(
    datos_cobranza: dict[str, Any],
    lineas_cobranza: list[dict[str, Any]],
    lineas_caja: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Crea una cobranza aplicada simple y confirmada.

    Contrato del primer corte:
    - ARS.
    - Una sola linea aplicada contra una FC/ND confirmada.
    - Cancelacion total del movimiento DEBE informado.
    - Una o mas lineas de caja.
    - Un solo asiento automatico tipo COBRANZA.
    - Impacto atomico en cobranza, caja, asiento y cuenta corriente.
    """

    def _operacion() -> dict[str, Any]:
        datos = _normalizar_datos_cobranza(datos_cobranza)
        cliente = _obtener_cliente_activo(datos["cliente_id"])
        cuenta_deudores_codigo = _obtener_cuenta_deudores_cliente(cliente)
        ejercicio = _obtener_ejercicio_para_cobranza(datos["fecha"])

        linea_aplicada = _normalizar_linea_cobranza_aplicada(
            datos,
            lineas_cobranza,
            cuenta_deudores_codigo,
        )
        lineas_caja_normalizadas = _normalizar_lineas_caja(
            datos,
            lineas_caja,
        )

        _validar_totales(datos, linea_aplicada, lineas_caja_normalizadas)

        descripcion = _descripcion_cobranza(datos, cliente)

        asiento = crear_asiento_contable_automatico_confirmado(
            {
                "ejercicio_id": ejercicio["id"],
                "fecha": datos["fecha"],
                "descripcion": descripcion,
                "tipo": _TIPO_ASIENTO_COBRANZA,
                "cotizacion_tipo": "CIERRE",
            },
            _armar_detalles_asiento_cobranza(
                descripcion,
                cuenta_deudores_codigo,
                lineas_caja_normalizadas,
                datos["total_centavos"],
            ),
        )

        cobranza = crear_cobranza_cliente(
            {
                "cliente_id": datos["cliente_id"],
                "fecha": datos["fecha"],
                "tipo_cobranza": _TIPO_COBRANZA_APLICADA,
                "tipo_comprobante": _TIPO_COMPROBANTE_RECIBO,
                "letra": datos["letra"],
                "punto_venta": datos["punto_venta"],
                "numero": datos["numero"],
                "moneda_codigo": _MONEDA_CONTABLE,
                "cotizacion_1000000": _ESCALA_COTIZACION_CONTABLE,
                "total_centavos": datos["total_centavos"],
                "estado": "CONFIRMADO",
                "asiento_id": asiento["id"],
                "observaciones": datos["observaciones"],
            },
            [
                {
                    "tipo_linea": linea_aplicada["tipo_linea"],
                    "movimiento_ctacte_cancelado_id": linea_aplicada[
                        "movimiento_ctacte_cancelado_id"
                    ],
                    "venta_comprobante_id": linea_aplicada["venta_comprobante_id"],
                    "importe_centavos": linea_aplicada["importe_centavos"],
                    "cuenta_cancelacion_codigo": cuenta_deudores_codigo,
                    "orden": 1,
                    "observaciones": linea_aplicada["observaciones"],
                }
            ],
        )

        movimiento_caja = crear_movimiento_caja(
            {
                "fecha": datos["fecha"],
                "tipo_movimiento": _TIPO_MOVIMIENTO_CAJA_INGRESO,
                "origen_tipo": _ORIGEN_CLIENTE_COBRANZA,
                "origen_id": cobranza["id"],
                "moneda_contable_codigo": _MONEDA_CONTABLE,
                "total_contable_centavos": datos["total_centavos"],
                "estado": "CONFIRMADO",
                "asiento_id": asiento["id"],
                "observaciones": descripcion,
            },
            lineas_caja_normalizadas,
        )

        movimiento_cuenta_corriente = crear_movimiento_haber_cliente(
            {
                "cliente_id": datos["cliente_id"],
                "fecha": datos["fecha"],
                "tipo_movimiento": "COBRANZA",
                "descripcion": _descripcion_movimiento_ctacte(cobranza),
                "moneda_codigo": _MONEDA_CONTABLE,
                "estado": "CONFIRMADO",
                "origen_tipo": _ORIGEN_CLIENTE_COBRANZA,
                "origen_id": cobranza["id"],
                "asiento_id": asiento["id"],
                "importe_centavos": datos["total_centavos"],
            }
        )

        vincular_linea_cobranza_movimiento_ctacte_generado(
            cobranza["lineas"][0]["id"],
            movimiento_cuenta_corriente["id"],
        )

        cobranza_actualizada = obtener_cobranza_cliente_por_id(cobranza["id"])

        if cobranza_actualizada is None:
            raise ValueError("No se pudo recuperar la cobranza confirmada.")

        return {
            "cobranza": cobranza_actualizada,
            "movimiento_caja": movimiento_caja,
            "asiento": asiento,
            "movimiento_cuenta_corriente": movimiento_cuenta_corriente,
        }

    return ejecutar_en_transaccion(_operacion)


def _normalizar_datos_cobranza(datos_cobranza: dict[str, Any]) -> dict[str, Any]:
    datos = _copiar_dict(datos_cobranza, "Los datos de cobranza son obligatorios.")

    tipo_cobranza = str(datos.get("tipo_cobranza", _TIPO_COBRANZA_APLICADA) or "").strip().upper()
    if tipo_cobranza != _TIPO_COBRANZA_APLICADA:
        raise ValueError("Este service solo confirma cobranzas aplicadas simples.")

    moneda_codigo = str(datos.get("moneda_codigo", _MONEDA_CONTABLE) or "").strip().upper()
    if moneda_codigo != _MONEDA_CONTABLE:
        raise ValueError("Este service solo confirma cobranzas en ARS.")

    fecha = _validar_fecha_iso(datos.get("fecha"), "La fecha de cobranza es obligatoria.")

    return {
        "cliente_id": _validar_entero_positivo(
            datos.get("cliente_id"),
            "El cliente es obligatorio.",
        ),
        "fecha": fecha,
        "tipo_cobranza": tipo_cobranza,
        "letra": _normalizar_letra(datos.get("letra", _LETRA_RECIBO_DEFAULT)),
        "punto_venta": _validar_entero_no_negativo(
            datos.get("punto_venta", 0),
            "El punto de venta debe ser no negativo.",
        ),
        "numero": _validar_entero_no_negativo(
            datos.get("numero", 0),
            "El numero debe ser no negativo.",
        ),
        "moneda_codigo": moneda_codigo,
        "total_centavos": _validar_entero_positivo(
            datos.get("total_centavos"),
            "El total de cobranza debe ser mayor a cero.",
        ),
        "observaciones": _normalizar_texto_opcional(datos.get("observaciones")),
    }


def _normalizar_linea_cobranza_aplicada(
    datos_cobranza: dict[str, Any],
    lineas_cobranza: list[dict[str, Any]],
    cuenta_deudores_codigo: str,
) -> dict[str, Any]:
    lineas = list(lineas_cobranza or [])

    if len(lineas) != 1:
        raise ValueError("La cobranza aplicada simple debe tener exactamente una linea.")

    linea = _copiar_dict(lineas[0], "La linea de cobranza es obligatoria.")
    movimiento_id = _validar_entero_positivo(
        linea.get("movimiento_ctacte_cancelado_id"),
        "El movimiento de cuenta corriente cancelado es obligatorio.",
    )
    comprobante_id = _validar_entero_positivo(
        linea.get("venta_comprobante_id"),
        "El comprobante de venta cancelado es obligatorio.",
    )
    importe_centavos = _validar_entero_positivo(
        linea.get("importe_centavos"),
        "El importe aplicado debe ser mayor a cero.",
    )

    movimiento = obtener_movimiento_cliente_cuenta_corriente_por_id(movimiento_id)
    if movimiento is None:
        raise ValueError("No existe el movimiento de cuenta corriente cancelado.")

    comprobante = obtener_venta_comprobante_por_id(comprobante_id)
    if comprobante is None:
        raise ValueError("No existe el comprobante de venta cancelado.")

    _validar_movimiento_cancelable(
        datos_cobranza,
        movimiento,
        comprobante,
        importe_centavos,
    )

    tipo_linea = str(linea.get("tipo_linea", comprobante["tipo_comprobante"]) or "").strip().upper()
    if tipo_linea != comprobante["tipo_comprobante"]:
        raise ValueError("El tipo de linea no coincide con el comprobante cancelado.")

    if tipo_linea not in {"FACTURA", "NOTA_DEBITO"}:
        raise ValueError("La cobranza aplicada solo puede cancelar FC o ND.")

    return {
        "tipo_linea": tipo_linea,
        "movimiento_ctacte_cancelado_id": movimiento["id"],
        "venta_comprobante_id": comprobante["id"],
        "importe_centavos": importe_centavos,
        "cuenta_cancelacion_codigo": cuenta_deudores_codigo,
        "observaciones": _normalizar_texto_opcional(linea.get("observaciones")),
    }


def _validar_movimiento_cancelable(
    datos_cobranza: dict[str, Any],
    movimiento: dict[str, Any],
    comprobante: dict[str, Any],
    importe_centavos: int,
) -> None:
    if int(movimiento["cliente_id"]) != int(datos_cobranza["cliente_id"]):
        raise ValueError("El movimiento cancelado no pertenece al cliente de la cobranza.")

    if int(comprobante["cliente_id"]) != int(datos_cobranza["cliente_id"]):
        raise ValueError("El comprobante cancelado no pertenece al cliente de la cobranza.")

    if movimiento["estado"] != "CONFIRMADO":
        raise ValueError("Solo se pueden cancelar movimientos confirmados.")

    if movimiento["lado"] != "DEBE":
        raise ValueError("La cobranza aplicada solo puede cancelar movimientos al DEBE.")

    if movimiento["tipo_movimiento"] not in {"FACTURA", "NOTA_DEBITO"}:
        raise ValueError("La cobranza aplicada solo puede cancelar FC o ND.")

    if movimiento.get("origen_tipo") != _ORIGEN_VENTA_COMPROBANTE:
        raise ValueError("El movimiento cancelado no proviene de un comprobante de venta.")

    if int(movimiento.get("origen_id") or 0) != int(comprobante["id"]):
        raise ValueError("El movimiento cancelado no corresponde al comprobante informado.")

    if comprobante["estado"] != "CONFIRMADO":
        raise ValueError("El comprobante cancelado debe estar CONFIRMADO.")

    if comprobante["tipo_comprobante"] not in {"FACTURA", "NOTA_DEBITO"}:
        raise ValueError("La cobranza aplicada solo puede cancelar FC o ND.")

    if comprobante["moneda_codigo"] != _MONEDA_CONTABLE:
        raise ValueError("Este service solo cancela comprobantes en ARS.")

    if int(movimiento["importe_centavos"]) != importe_centavos:
        raise ValueError("El primer corte solo permite cancelacion total del movimiento.")

    if int(comprobante["total_centavos"]) != importe_centavos:
        raise ValueError("El importe aplicado debe coincidir con el total del comprobante.")


def _normalizar_lineas_caja(
    datos_cobranza: dict[str, Any],
    lineas_caja: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lineas = list(lineas_caja or [])

    if not lineas:
        raise ValueError("La cobranza debe tener al menos una linea de caja.")

    lineas_normalizadas = []

    for indice, linea_original in enumerate(lineas, start=1):
        linea = _copiar_dict(linea_original, "La linea de caja es obligatoria.")
        codigo_medio = _validar_texto_obligatorio(
            linea.get("medio_operativo_codigo"),
            f"El medio operativo de la linea {indice} es obligatorio.",
        ).upper()

        medio = obtener_medio_operativo_por_codigo(codigo_medio)
        if medio is None or not medio.get("esta_activo"):
            raise ValueError(f"El medio operativo de la linea {indice} no existe o no esta activo.")

        if medio["moneda_codigo"] != _MONEDA_CONTABLE:
            raise ValueError("Este service solo acepta lineas de caja en ARS.")

        importe_centavos = _validar_entero_positivo(
            linea.get(
                "importe_contable_centavos",
                linea.get("importe_centavos", linea.get("importe_nominal_centavos")),
            ),
            f"El importe de caja de la linea {indice} debe ser positivo.",
        )
        cotizacion_1000000 = _validar_entero_positivo(
            linea.get("cotizacion_1000000", _ESCALA_COTIZACION_CONTABLE),
            "La cotizacion de caja debe ser positiva.",
        )

        if cotizacion_1000000 != _ESCALA_COTIZACION_CONTABLE:
            raise ValueError("La cotizacion ARS de caja debe ser 1000000.")

        lineas_normalizadas.append(
            {
                "medio_operativo_codigo": medio["codigo"],
                "cuenta_contable_codigo": medio["cuenta_contable_codigo"],
                "moneda_codigo": _MONEDA_CONTABLE,
                "fecha_valor": _validar_fecha_iso_opcional(
                    linea.get("fecha_valor"),
                    datos_cobranza["fecha"],
                ),
                "referencia": _normalizar_texto_opcional(linea.get("referencia")),
                "importe_nominal_centavos": importe_centavos,
                "cotizacion_1000000": _ESCALA_COTIZACION_CONTABLE,
                "importe_contable_centavos": importe_centavos,
                "detalle": _normalizar_texto_opcional(linea.get("detalle")),
                "orden": _validar_entero_no_negativo(
                    linea.get("orden", indice),
                    "El orden de caja debe ser no negativo.",
                ),
            }
        )

    return lineas_normalizadas


def _validar_totales(
    datos_cobranza: dict[str, Any],
    linea_aplicada: dict[str, Any],
    lineas_caja: list[dict[str, Any]],
) -> None:
    total_cobranza = int(datos_cobranza["total_centavos"])
    total_aplicado = int(linea_aplicada["importe_centavos"])
    total_caja = sum(int(linea["importe_contable_centavos"]) for linea in lineas_caja)

    if total_aplicado != total_cobranza:
        raise ValueError("El total aplicado no coincide con el total de cobranza.")

    if total_caja != total_cobranza:
        raise ValueError("El total de caja no coincide con el total de cobranza.")


def _armar_detalles_asiento_cobranza(
    descripcion: str,
    cuenta_deudores_codigo: str,
    lineas_caja: list[dict[str, Any]],
    total_centavos: int,
) -> list[dict[str, Any]]:
    detalles = []

    for indice, linea in enumerate(lineas_caja, start=1):
        detalles.append(
            _crear_renglon_asiento(
                cuenta_contable_codigo=linea["cuenta_contable_codigo"],
                descripcion=f"{descripcion} | Medio {linea['medio_operativo_codigo']}",
                debe_centavos=int(linea["importe_contable_centavos"]),
                haber_centavos=0,
                renglon=indice,
            )
        )

    detalles.append(
        _crear_renglon_asiento(
            cuenta_contable_codigo=cuenta_deudores_codigo,
            descripcion=descripcion,
            debe_centavos=0,
            haber_centavos=int(total_centavos),
            renglon=len(detalles) + 1,
        )
    )

    return detalles


def _crear_renglon_asiento(
    cuenta_contable_codigo: str,
    descripcion: str,
    debe_centavos: int,
    haber_centavos: int,
    renglon: int,
) -> dict[str, Any]:
    return {
        "renglon": renglon,
        "cuenta_contable_codigo": cuenta_contable_codigo,
        "descripcion": descripcion,
        "moneda_codigo": _MONEDA_CONTABLE,
        "cotizacion_1000000": _ESCALA_COTIZACION_CONTABLE,
        "nominal_debe_centavos": debe_centavos,
        "nominal_haber_centavos": haber_centavos,
        "debe_centavos": debe_centavos,
        "haber_centavos": haber_centavos,
    }


def _obtener_cliente_activo(cliente_id: int) -> dict[str, Any]:
    validar_cliente_activo(cliente_id)
    cliente = obtener_cliente_por_id(cliente_id)

    if cliente is None or not cliente.get("esta_activo"):
        raise ValueError("El cliente no existe o no esta activo.")

    return cliente


def _obtener_cuenta_deudores_cliente(cliente: dict[str, Any]) -> str:
    return _validar_texto_obligatorio(
        cliente.get("cuenta_deudores_ventas_codigo"),
        "El cliente no tiene cuenta de deudores por ventas configurada.",
    )


def _obtener_ejercicio_para_cobranza(fecha: str) -> dict[str, Any]:
    ejercicio = obtener_ejercicio_contable_por_fecha(fecha)

    if ejercicio is None:
        raise ValueError("No existe ejercicio contable para la fecha de cobranza.")

    if ejercicio["estado"] != "ABIERTO":
        raise ValueError("El ejercicio contable de la cobranza no esta abierto.")

    if int(ejercicio["bloqueado"]) == 1:
        raise ValueError("El ejercicio contable de la cobranza esta bloqueado.")

    return ejercicio


def _descripcion_cobranza(datos_cobranza: dict[str, Any], cliente: dict[str, Any]) -> str:
    recibo = _descripcion_recibo(datos_cobranza)
    return f"Cobranza {recibo} | Sujeto: {cliente['razon_social']}"


def _descripcion_movimiento_ctacte(cobranza: dict[str, Any]) -> str:
    return _descripcion_recibo(cobranza)


def _descripcion_recibo(datos: dict[str, Any]) -> str:
    return (
        f"RC {datos['letra']} "
        f"{int(datos['punto_venta']):04d}-{int(datos['numero']):08d}"
    )


def _copiar_dict(valor: Any, mensaje: str) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise ValueError(mensaje)

    return dict(valor)


def _validar_fecha_iso(valor: Any, mensaje: str) -> str:
    fecha = str(valor or "").strip()

    if not _PATRON_FECHA_ISO.match(fecha):
        raise ValueError(mensaje)

    try:
        date.fromisoformat(fecha)
    except ValueError as exc:
        raise ValueError("La fecha debe ser valida.") from exc

    return fecha


def _validar_fecha_iso_opcional(valor: Any, default: str) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return default

    return _validar_fecha_iso(texto, "La fecha valor debe ser ISO.")


def _validar_entero_positivo(valor: Any, mensaje: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje)

    try:
        entero = int(str(valor).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(mensaje) from exc

    if entero <= 0:
        raise ValueError(mensaje)

    return entero


def _validar_entero_no_negativo(valor: Any, mensaje: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje)

    try:
        entero = int(str(valor).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(mensaje) from exc

    if entero < 0:
        raise ValueError(mensaje)

    return entero


def _validar_texto_obligatorio(valor: Any, mensaje: str) -> str:
    texto = str(valor or "").strip()

    if not texto:
        raise ValueError(mensaje)

    return texto


def _normalizar_texto_opcional(valor: Any) -> str | None:
    texto = str(valor or "").strip()
    return texto or None


def _normalizar_letra(valor: Any) -> str:
    return _validar_texto_obligatorio(valor, "La letra del recibo es obligatoria.").upper()
