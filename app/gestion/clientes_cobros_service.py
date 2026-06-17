from datetime import date
from typing import Any

from app.caja.intenciones_caja_repository import crear_intencion_caja
from app.gestion.clientes_cobranzas_repository import (
    obtener_proximo_numero_cobranza,
    obtener_total_confirmado_aplicado_a_movimiento,
)
from app.gestion.clientes_cuenta_corriente_repository import (
    listar_movimientos_cliente_cuenta_corriente,
)
from app.gestion.clientes_repository import obtener_cliente_por_id, validar_cliente_activo
from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
    normalizar_decimal_argentino_a_entero_escala,
    normalizar_fecha_argentina_a_iso,
)

_TIPOS_COBRABLES = {"FACTURA", "NOTA_DEBITO"}
_TIPO_RECIBO = "RC"
_LETRA_RECIBO = "C"
_PUNTO_VENTA_DEFAULT = 1
_MONEDA_CONTABLE = "ARS"
_ORIGEN_RECIBO_CLIENTE = "RECIBO_CLIENTE"


def obtener_contexto_formulario_cobro_cliente(cliente_id: Any) -> dict[str, Any]:
    """
    Devuelve contexto para preparar una intencion de cobro de cliente.

    No confirma cobranza, caja, asiento ni cuenta corriente. Solo prepara el
    origen y permite continuar a la pantalla transversal de caja.
    """
    cliente_id_normalizado = _normalizar_id(cliente_id)
    cliente = obtener_cliente_por_id(cliente_id_normalizado)

    if cliente is None:
        raise ValueError("No existe el cliente informado.")

    validar_cliente_activo(cliente_id_normalizado)

    comprobantes_cobrables = _listar_comprobantes_cobrables(cliente_id_normalizado)

    total_saldo_centavos = sum(
        int(comprobante["saldo_comprobante_centavos"])
        for comprobante in comprobantes_cobrables
    )

    proximo_numero = obtener_proximo_numero_cobranza(
        "RECIBO",
        _LETRA_RECIBO,
        _PUNTO_VENTA_DEFAULT,
    )
    numero_preview = _formatear_numero_recibo(
        _TIPO_RECIBO,
        _LETRA_RECIBO,
        _PUNTO_VENTA_DEFAULT,
        proximo_numero,
    )

    return {
        "cliente": cliente,
        "cobro_form": {
            "tipo_operacion": "RECIBO",
            "tipo_comprobante": _TIPO_RECIBO,
            "letra": _LETRA_RECIBO,
            "punto_venta": str(_PUNTO_VENTA_DEFAULT),
            "numero": str(proximo_numero),
            "numero_preview": numero_preview,
            "moneda_codigo": _MONEDA_CONTABLE,
            "fecha": date.today().strftime("%d/%m/%Y"),
            "observaciones": "",
        },
        "comprobantes_cobrables": comprobantes_cobrables,
        "cantidad_comprobantes_cobrables": len(comprobantes_cobrables),
        "total_saldo_cobrable_centavos": total_saldo_centavos,
        "total_saldo_cobrable_argentina": _formatear_centavos(total_saldo_centavos),
    }


def crear_intencion_cobro_cliente_desde_formulario(
    cliente_id: Any,
    formulario: Any,
) -> dict[str, Any]:
    """
    Crea una intencion pendiente para confirmar luego desde caja transversal.

    Contrato primer corte:
    - un solo comprobante seleccionado;
    - cancelacion total;
    - ARS;
    - no genera impacto definitivo.
    """
    cliente_id_normalizado = _normalizar_id(cliente_id)
    cliente_id_formulario = _normalizar_id(
        _obtener_valor_formulario(formulario, "cliente_id", cliente_id_normalizado)
    )

    if cliente_id_formulario != cliente_id_normalizado:
        raise ValueError("El cliente del formulario no coincide con la ruta.")

    fecha_argentina = _obtener_valor_formulario(formulario, "fecha")
    fecha_iso = _normalizar_fecha_argentina(
        fecha_argentina,
        "La fecha de cobro es obligatoria.",
    )

    movimiento_id = _obtener_unico_movimiento_seleccionado(formulario)
    importe_centavos = _normalizar_importe_argentino(
        _obtener_valor_formulario(
            formulario,
            f"importe_a_cobrar_{movimiento_id}",
        ),
        "El importe a cobrar debe respetar formato argentino 9.999,99.",
    )
    venta_comprobante_id = _normalizar_id(
        _obtener_valor_formulario(
            formulario,
            f"venta_comprobante_id_{movimiento_id}",
        )
    )
    tipo_movimiento = _validar_tipo_cobrable(
        _obtener_valor_formulario(
            formulario,
            f"tipo_movimiento_{movimiento_id}",
            "FACTURA",
        )
    )

    letra = _validar_texto_obligatorio(
        _obtener_valor_formulario(formulario, "letra", _LETRA_RECIBO),
        "La letra del recibo es obligatoria.",
    ).upper()

    punto_venta = _normalizar_entero_no_negativo(
        _obtener_valor_formulario(formulario, "punto_venta", _PUNTO_VENTA_DEFAULT),
        "El punto de venta debe ser no negativo.",
    )
    numero = obtener_proximo_numero_cobranza("RECIBO", letra, punto_venta)
    observaciones = _normalizar_texto_opcional(
        _obtener_valor_formulario(formulario, "observaciones", "")
    )

    comprobante_cobrable = _obtener_comprobante_cobrable_por_movimiento_id(
        cliente_id_normalizado,
        movimiento_id,
    )
    if comprobante_cobrable is None:
        raise ValueError("El comprobante seleccionado no tiene saldo abierto para cobrar.")

    if int(comprobante_cobrable["venta_comprobante_id"] or 0) != venta_comprobante_id:
        raise ValueError("El comprobante seleccionado no coincide con la cuenta corriente.")

    if comprobante_cobrable["tipo_movimiento"] != tipo_movimiento:
        raise ValueError("El tipo de movimiento seleccionado no coincide con el comprobante.")

    saldo_abierto_centavos = int(comprobante_cobrable["saldo_comprobante_centavos"])
    if importe_centavos != saldo_abierto_centavos:
        raise ValueError("El primer corte solo permite cobrar el saldo total abierto del comprobante.")

    return crear_intencion_caja(
        {
            "origen_tipo": _ORIGEN_RECIBO_CLIENTE,
            "tipo_movimiento": "INGRESO",
            "total_esperado_centavos": importe_centavos,
            "observaciones": "Recibo cliente pendiente",
            "origen_payload": {
                "origen_tipo": _ORIGEN_RECIBO_CLIENTE,
                "origen_descripcion": _formatear_numero_recibo(
                    _TIPO_RECIBO,
                    letra,
                    punto_venta,
                    numero,
                ),
                "datos_cobranza": {
                    "cliente_id": cliente_id_normalizado,
                    "fecha": fecha_iso,
                    "tipo_cobranza": "APLICADA",
                    "letra": letra,
                    "punto_venta": punto_venta,
                    "numero": numero,
                    "moneda_codigo": _MONEDA_CONTABLE,
                    "total_centavos": importe_centavos,
                    "observaciones": observaciones,
                },
                "lineas_cobranza": [
                    {
                        "tipo_linea": tipo_movimiento,
                        "movimiento_ctacte_cancelado_id": movimiento_id,
                        "venta_comprobante_id": venta_comprobante_id,
                        "importe_centavos": importe_centavos,
                    }
                ],
            },
        }
    )


def _listar_comprobantes_cobrables(cliente_id: int) -> list[dict[str, Any]]:
    movimientos = listar_movimientos_cliente_cuenta_corriente(
        cliente_id,
        estado="CONFIRMADO",
    )
    comprobantes = []

    for movimiento in movimientos:
        tipo_movimiento = str(movimiento.get("tipo_movimiento") or "").strip().upper()
        debe_centavos = int(movimiento.get("debe_centavos") or 0)

        if tipo_movimiento not in _TIPOS_COBRABLES:
            continue

        if debe_centavos <= 0:
            continue

        total_aplicado_centavos = obtener_total_confirmado_aplicado_a_movimiento(
            movimiento["id"],
        )
        saldo_abierto_centavos = debe_centavos - total_aplicado_centavos

        if saldo_abierto_centavos <= 0:
            continue

        comprobantes.append(
            {
                "movimiento_id": movimiento["id"],
                "venta_comprobante_id": movimiento.get("origen_id"),
                "origen_id": movimiento.get("origen_id"),
                "tipo_movimiento": tipo_movimiento,
                "comprobante_mostrar": _mostrar_detalle_comprobante(movimiento),
                "fecha_argentina": _formatear_fecha(movimiento.get("fecha")),
                "vencimiento_argentina": "",
                "saldo_comprobante_centavos": saldo_abierto_centavos,
                "saldo_comprobante_argentina": _formatear_centavos(saldo_abierto_centavos),
                "importe_sugerido_argentina": _formatear_centavos(saldo_abierto_centavos),
            }
        )

    return comprobantes


def _obtener_comprobante_cobrable_por_movimiento_id(
    cliente_id: int,
    movimiento_id: Any,
) -> dict[str, Any] | None:
    movimiento_id_normalizado = _normalizar_id(movimiento_id)

    for comprobante in _listar_comprobantes_cobrables(cliente_id):
        if int(comprobante["movimiento_id"]) == movimiento_id_normalizado:
            return comprobante

    return None


def _obtener_unico_movimiento_seleccionado(formulario: Any) -> int:
    seleccionados = [
        str(valor or "").strip()
        for valor in _obtener_lista_formulario(
            formulario,
            "movimientos_ctacte_cancelados",
        )
        if str(valor or "").strip()
    ]

    if len(seleccionados) != 1:
        raise ValueError("Debe seleccionar exactamente un comprobante a cobrar.")

    return _normalizar_id(seleccionados[0])


def _obtener_valor_formulario(
    formulario: Any,
    campo: str,
    default: Any = "",
) -> Any:
    if formulario is None:
        return default

    if hasattr(formulario, "get"):
        return formulario.get(campo, default)

    return default


def _obtener_lista_formulario(formulario: Any, campo: str) -> list[Any]:
    if formulario is None:
        return []

    if hasattr(formulario, "getlist"):
        return list(formulario.getlist(campo))

    if hasattr(formulario, "get"):
        valor = formulario.get(campo)
        if valor is None:
            return []
        if isinstance(valor, (list, tuple)):
            return list(valor)
        return [valor]

    return []


def _normalizar_fecha_argentina(valor: Any, mensaje: str) -> str:
    texto = str(valor or "").strip()

    if not texto:
        raise ValueError(mensaje)

    try:
        return normalizar_fecha_argentina_a_iso(texto)
    except ValueError as exc:
        raise ValueError(mensaje) from exc


def _normalizar_importe_argentino(valor: Any, mensaje: str) -> int:
    texto = str(valor or "").strip()

    if not texto:
        raise ValueError(mensaje)

    try:
        importe_centavos = normalizar_decimal_argentino_a_entero_escala(texto, 2)
    except ValueError as exc:
        raise ValueError(mensaje) from exc

    if importe_centavos <= 0:
        raise ValueError("El importe debe ser mayor a cero.")

    return importe_centavos


def _validar_tipo_cobrable(valor: Any) -> str:
    tipo = str(valor or "").strip().upper()

    if tipo not in _TIPOS_COBRABLES:
        raise ValueError("La cobranza solo puede cancelar FC o ND.")

    return tipo


def _mostrar_detalle_comprobante(movimiento: dict[str, Any]) -> str:
    descripcion = str(movimiento.get("descripcion") or "").strip()

    if descripcion.startswith("Comprobante:"):
        comprobante = descripcion[len("Comprobante:"):].strip()
        if "|" in comprobante:
            comprobante = comprobante.split("|", 1)[0].strip()
        if comprobante:
            return comprobante

    tipo_movimiento = str(movimiento.get("tipo_movimiento") or "").strip().upper()
    prefijo = "FC" if tipo_movimiento == "FACTURA" else "ND"

    if descripcion:
        return f"{prefijo} {descripcion}".strip()

    return prefijo


def _formatear_numero_recibo(
    tipo: str,
    letra: str,
    punto_venta: int,
    numero: int,
) -> str:
    return f"{tipo} {letra} {int(punto_venta):04d}-{int(numero):08d}"


def _formatear_centavos(valor: Any) -> str:
    return formatear_entero_escala_a_decimal_argentino(int(valor or 0), 2)


def _formatear_fecha(fecha: Any) -> str:
    fecha_texto = str(fecha or "").strip()
    if not fecha_texto:
        return ""

    return formatear_fecha_iso_a_argentina(fecha_texto)


def _normalizar_id(valor: Any) -> int:
    try:
        valor_normalizado = int(str(valor or "").strip())
    except ValueError as exc:
        raise ValueError("El id informado es invalido.") from exc

    if valor_normalizado <= 0:
        raise ValueError("El id informado es invalido.")

    return valor_normalizado


def _normalizar_entero_no_negativo(valor: Any, mensaje: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje)

    try:
        valor_normalizado = int(str(valor or "").strip())
    except ValueError as exc:
        raise ValueError(mensaje) from exc

    if valor_normalizado < 0:
        raise ValueError(mensaje)

    return valor_normalizado


def _validar_texto_obligatorio(valor: Any, mensaje: str) -> str:
    texto = str(valor or "").strip()

    if not texto:
        raise ValueError(mensaje)

    return texto


def _normalizar_texto_opcional(valor: Any) -> str | None:
    texto = str(valor or "").strip()
    return texto or None
