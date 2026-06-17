from datetime import date
from typing import Any

from app.shared.formatos import formatear_entero_escala_a_decimal_argentino
from app.shared.medios_operativos_repository import listar_medios_operativos_activos

_TIPOS_MOVIMIENTO_VALIDOS = {"INGRESO", "EGRESO"}
_TIPO_MOVIMIENTO_DEFAULT = "INGRESO"
_ESTADO_WIP = "BORRADOR"
_NUMERO_PREVIEW_WIP = 1
_MONEDA_DEFAULT = "ARS"


def obtener_contexto_formulario_movimiento_caja(args: Any) -> dict[str, Any]:
    """
    Devuelve contexto WIP para Movimiento de Caja.

    No persiste cabecera, lineas, asiento ni origen funcional. Solo arma pantalla
    usando medios operativos activos.
    """
    tipo_movimiento = _normalizar_tipo_movimiento(
        _obtener_arg(args, "tipo_movimiento", _TIPO_MOVIMIENTO_DEFAULT)
    )
    total_esperado_centavos = _normalizar_entero_no_negativo(
        _obtener_arg(args, "total_esperado_centavos", 0)
    )
    cliente_id = _obtener_arg(args, "cliente_id", "")
    origen_tipo = _normalizar_texto_opcional(_obtener_arg(args, "origen_tipo", ""))
    origen_id = _normalizar_texto_opcional(_obtener_arg(args, "origen_id", ""))
    origen_descripcion = _normalizar_texto_opcional(
        _obtener_arg(args, "origen_descripcion", "")
    )

    medios_operativos = [
        _preparar_medio_operativo_para_formulario(medio)
        for medio in listar_medios_operativos_activos()
    ]

    return {
        "movimiento_form": {
            "tipo_movimiento": tipo_movimiento,
            "numero": str(_NUMERO_PREVIEW_WIP),
            "numero_preview": f"MC {_NUMERO_PREVIEW_WIP:08d}",
            "fecha": date.today().strftime("%d/%m/%Y"),
            "estado": _ESTADO_WIP,
            "tipo_motivo": "COBRO_CLIENTE" if origen_tipo else "MANUAL",
            "origen_tipo": origen_tipo or "",
            "origen_id": origen_id or "",
            "origen_descripcion": origen_descripcion or "",
            "cliente_id": cliente_id,
            "total_esperado_centavos": total_esperado_centavos,
            "total_esperado_argentina": _formatear_centavos(total_esperado_centavos),
            "moneda_codigo": _MONEDA_DEFAULT,
            "concepto": _armar_concepto(origen_descripcion),
        },
        "medios_operativos": medios_operativos,
        "cantidad_medios_operativos": len(medios_operativos),
    }


def _preparar_medio_operativo_para_formulario(medio: dict[str, Any]) -> dict[str, Any]:
    return {
        "codigo": medio["codigo"],
        "nombre": medio["nombre"],
        "descripcion_select": medio["descripcion_select"],
        "tipo": medio["tipo"],
        "moneda_codigo": medio["moneda_codigo"],
        "requiere_cotizacion": int(medio["requiere_cotizacion"]),
        "cotizacion_default_centavos": medio.get("cotizacion_default_centavos"),
        "banco_codigo": medio.get("banco_codigo") or "",
        "banco_nombre": medio.get("banco_nombre") or "",
        "plaza": medio.get("plaza") or "",
        "sucursal": medio.get("sucursal") or "",
        "numero_cuenta": medio.get("numero_cuenta") or "",
        "cuenta_contable_codigo": medio["cuenta_contable_codigo"],
        "cuenta_contable_descripcion": medio.get("cuenta_contable_descripcion") or "",
        "cuit": medio.get("cuit") or "",
    }


def _armar_concepto(origen_descripcion: str | None) -> str:
    if origen_descripcion:
        return f"Movimiento de caja generado desde {origen_descripcion}."

    return ""


def _normalizar_tipo_movimiento(valor: Any) -> str:
    tipo = str(valor or "").strip().upper()

    if tipo not in _TIPOS_MOVIMIENTO_VALIDOS:
        return _TIPO_MOVIMIENTO_DEFAULT

    return tipo


def _normalizar_entero_no_negativo(valor: Any) -> int:
    try:
        entero = int(str(valor or "0").strip())
    except ValueError:
        return 0

    return max(entero, 0)


def _normalizar_texto_opcional(valor: Any) -> str | None:
    texto = str(valor or "").strip()
    return texto or None


def _obtener_arg(args: Any, clave: str, default: Any = "") -> Any:
    if hasattr(args, "get"):
        return args.get(clave, default)

    return default


def _formatear_centavos(valor: Any) -> str:
    return formatear_entero_escala_a_decimal_argentino(int(valor or 0), 2)
