from datetime import date
from typing import Any

from app.gestion.clientes_cuenta_corriente_repository import (
    listar_movimientos_cliente_cuenta_corriente,
)
from app.gestion.clientes_repository import obtener_cliente_por_id, validar_cliente_activo
from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
)

_TIPOS_COBRABLES = {"FACTURA", "NOTA_DEBITO"}
_TIPO_RECIBO = "RC"
_LETRA_RECIBO = "C"
_PUNTO_VENTA_DEFAULT = 1
_NUMERO_PREVIEW_WIP = 1
_MONEDA_CONTABLE = "ARS"


def obtener_contexto_formulario_cobro_cliente(cliente_id: Any) -> dict[str, Any]:
    """
    Devuelve contexto WIP para el formulario visual de cobro de cliente.

    Este WIP no persiste recibos, aplicaciones ni movimientos de caja.
    Solo prepara la imputacion visual de comprobantes cobrables.
    """
    cliente_id_normalizado = _normalizar_id(cliente_id)
    cliente = obtener_cliente_por_id(cliente_id_normalizado)

    if cliente is None:
        raise ValueError("No existe el cliente informado.")

    validar_cliente_activo(cliente_id_normalizado)

    comprobantes_cobrables = _listar_comprobantes_cobrables_wip(cliente_id_normalizado)

    total_saldo_centavos = sum(
        int(comprobante["saldo_comprobante_centavos"])
        for comprobante in comprobantes_cobrables
    )

    numero_preview = _formatear_numero_recibo(
        _TIPO_RECIBO,
        _LETRA_RECIBO,
        _PUNTO_VENTA_DEFAULT,
        _NUMERO_PREVIEW_WIP,
    )

    return {
        "cliente": cliente,
        "cobro_form": {
            "tipo_operacion": "RECIBO",
            "tipo_comprobante": _TIPO_RECIBO,
            "letra": _LETRA_RECIBO,
            "punto_venta": str(_PUNTO_VENTA_DEFAULT),
            "numero": str(_NUMERO_PREVIEW_WIP),
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


def _listar_comprobantes_cobrables_wip(cliente_id: int) -> list[dict[str, Any]]:
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

        comprobantes.append(
            {
                "movimiento_id": movimiento["id"],
                "origen_id": movimiento.get("origen_id"),
                "tipo_movimiento": tipo_movimiento,
                "comprobante_mostrar": _mostrar_detalle_comprobante(movimiento),
                "fecha_argentina": _formatear_fecha(movimiento.get("fecha")),
                "vencimiento_argentina": "",
                "saldo_comprobante_centavos": debe_centavos,
                "saldo_comprobante_argentina": _formatear_centavos(debe_centavos),
                "importe_sugerido_argentina": _formatear_centavos(debe_centavos),
            }
        )

    return comprobantes


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
        raise ValueError("El cliente informado es invalido.") from exc

    if valor_normalizado <= 0:
        raise ValueError("El cliente informado es invalido.")

    return valor_normalizado
