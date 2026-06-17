from datetime import date
import re
from typing import Any

from app.caja.intenciones_caja_repository import (
    marcar_intencion_caja_confirmada,
    obtener_intencion_caja_por_id,
)
from app.caja.movimientos_caja_repository import (
    listar_movimientos_caja,
    obtener_movimiento_caja_por_id,
)
from app.gestion.clientes_cobranzas_service import crear_cobranza_aplicada_confirmada
from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
    normalizar_decimal_argentino_a_entero_escala,
    normalizar_fecha_argentina_a_iso,
)
from app.shared.medios_operativos_repository import listar_medios_operativos_activos
from app.shared.transacciones_repository import ejecutar_en_transaccion

_TIPOS_MOVIMIENTO_VALIDOS = {"INGRESO", "EGRESO"}
_TIPO_MOVIMIENTO_DEFAULT = "INGRESO"
_ESTADO_PENDIENTE = "PENDIENTE"
_NUMERO_PREVIEW_WIP = 1
_MONEDA_DEFAULT = "ARS"
_ORIGEN_RECIBO_CLIENTE = "RECIBO_CLIENTE"
_RESULTADO_CLIENTE_COBRANZA = "CLIENTE_COBRANZA"
_LINEA_FORM_RE = re.compile(r"^lineas\[(\d+)\]\[([^\]]+)\]$")


def obtener_contexto_formulario_movimiento_caja(args: Any) -> dict[str, Any]:
    """
    Devuelve contexto para la pantalla transversal de caja.

    Con intencion_id: carga un origen pendiente y no impacta nada hasta POST.
    Sin intencion_id: mantiene contexto manual visual para futuros cortes.
    """
    intencion_id = _normalizar_entero_positivo_opcional(_obtener_arg(args, "intencion_id", ""))
    intencion = None
    payload = {}

    if intencion_id is not None:
        intencion = obtener_intencion_caja_por_id(intencion_id)
        if intencion is None:
            raise ValueError("No existe la intencion de caja informada.")
        if intencion["estado"] != _ESTADO_PENDIENTE:
            raise ValueError("La intencion de caja no esta pendiente.")
        payload = dict(intencion["origen_payload"])

    tipo_movimiento = _normalizar_tipo_movimiento(
        intencion["tipo_movimiento"] if intencion else _obtener_arg(args, "tipo_movimiento", _TIPO_MOVIMIENTO_DEFAULT)
    )
    total_esperado_centavos = (
        int(intencion["total_esperado_centavos"])
        if intencion
        else _normalizar_entero_no_negativo(_obtener_arg(args, "total_esperado_centavos", 0))
    )

    origen_tipo = (
        intencion["origen_tipo"]
        if intencion
        else _normalizar_texto_opcional(_obtener_arg(args, "origen_tipo", ""))
    )
    origen_id = str(intencion["id"]) if intencion else _normalizar_texto_opcional(_obtener_arg(args, "origen_id", ""))
    origen_descripcion = (
        _normalizar_texto_opcional(payload.get("origen_descripcion"))
        if intencion
        else _normalizar_texto_opcional(_obtener_arg(args, "origen_descripcion", ""))
    )
    datos_cobranza = payload.get("datos_cobranza") if isinstance(payload.get("datos_cobranza"), dict) else {}
    cliente_id = (
        str(datos_cobranza.get("cliente_id") or "")
        if intencion
        else _obtener_arg(args, "cliente_id", "")
    )
    fecha_formulario = _fecha_argentina_desde_payload(payload) if intencion else date.today().strftime("%d/%m/%Y")

    medios_operativos = [
        _preparar_medio_operativo_para_formulario(medio)
        for medio in listar_medios_operativos_activos()
    ]

    return {
        "movimiento_form": {
            "intencion_id": intencion["id"] if intencion else "",
            "tipo_movimiento": tipo_movimiento,
            "numero": str(_NUMERO_PREVIEW_WIP),
            "numero_preview": f"MC {_NUMERO_PREVIEW_WIP:08d}",
            "fecha": fecha_formulario,
            "estado": _ESTADO_PENDIENTE if intencion else "BORRADOR",
            "tipo_motivo": origen_tipo or "MANUAL",
            "origen_tipo": origen_tipo or "",
            "origen_id": origen_id or "",
            "origen_descripcion": origen_descripcion or "",
            "cliente_id": cliente_id,
            "total_esperado_centavos": total_esperado_centavos,
            "total_esperado_argentina": _formatear_centavos(total_esperado_centavos),
            "moneda_codigo": _MONEDA_DEFAULT,
            "concepto": _armar_concepto(origen_descripcion),
            "titulo_pantalla": _titulo_formulario_caja(tipo_movimiento, origen_tipo),
            "descripcion_pantalla": _descripcion_formulario_caja(tipo_movimiento, origen_tipo),
            "resumen_operacion": _resumen_operacion_formulario_caja(
                tipo_movimiento,
                origen_tipo,
                origen_descripcion,
            ),
            "total_label": _total_label_formulario_caja(tipo_movimiento, origen_tipo),
            "medios_titulo": _medios_titulo_formulario_caja(tipo_movimiento),
            "medios_subtitulo": _medios_subtitulo_formulario_caja(tipo_movimiento),
            "confirmar_label": _confirmar_label_formulario_caja(tipo_movimiento, origen_tipo),
            "tipo_movimiento_mostrar": _tipo_movimiento_mostrar(tipo_movimiento),
            "estado_mostrar": _estado_formulario_mostrar(_ESTADO_PENDIENTE if intencion else "BORRADOR"),
            "origen_tipo_mostrar": _origen_tipo_formulario_mostrar(origen_tipo),
            "ayuda_confirmacion": _ayuda_confirmacion_formulario_caja(tipo_movimiento, origen_tipo),
        },
        "medios_operativos": medios_operativos,
        "cantidad_medios_operativos": len(medios_operativos),
    }


def confirmar_movimiento_caja_desde_formulario(formulario: Any) -> dict[str, Any]:
    """
    Confirma una intencion desde caja transversal.

    Primer origen soportado: RECIBO_CLIENTE.
    """
    intencion_id = _validar_entero_positivo(
        _obtener_valor_formulario(formulario, "intencion_id"),
        "La intencion de caja es obligatoria.",
    )
    intencion = obtener_intencion_caja_por_id(intencion_id)

    if intencion is None:
        raise ValueError("No existe la intencion de caja informada.")

    if intencion["estado"] != _ESTADO_PENDIENTE:
        raise ValueError("La intencion de caja no esta pendiente.")

    origen_tipo = str(intencion["origen_tipo"] or "").strip().upper()
    if origen_tipo != _ORIGEN_RECIBO_CLIENTE:
        raise ValueError("El origen de caja aun no esta soportado.")

    payload = dict(intencion["origen_payload"])
    datos_cobranza = _copiar_dict(
        payload.get("datos_cobranza"),
        "La intencion no contiene datos de cobranza.",
    )
    lineas_cobranza = _copiar_lista(
        payload.get("lineas_cobranza"),
        "La intencion no contiene lineas de cobranza.",
    )
    fecha_caja = _normalizar_fecha_argentina(
        _obtener_valor_formulario(formulario, "fecha"),
        "La fecha del movimiento de caja es obligatoria.",
    )

    datos_cobranza["fecha"] = fecha_caja

    lineas_caja = _extraer_lineas_caja_desde_formulario(formulario, fecha_caja)
    total_lineas = sum(int(linea["importe_centavos"]) for linea in lineas_caja)

    if total_lineas != int(intencion["total_esperado_centavos"]):
        raise ValueError("El total de lineas de caja no coincide con el total esperado.")

    def _operacion() -> dict[str, Any]:
        resultado = crear_cobranza_aplicada_confirmada(
            datos_cobranza,
            lineas_cobranza,
            lineas_caja,
        )
        intencion_confirmada = marcar_intencion_caja_confirmada(
            intencion_id,
            resultado_tipo=_RESULTADO_CLIENTE_COBRANZA,
            resultado_id=resultado["cobranza"]["id"],
        )

        return {
            "origen_tipo": origen_tipo,
            "resultado_tipo": _RESULTADO_CLIENTE_COBRANZA,
            "cliente_id": int(datos_cobranza["cliente_id"]),
            "cobranza_id": resultado["cobranza"]["id"],
            "movimiento_caja_id": resultado["movimiento_caja"]["id"],
            "asiento_id": resultado["asiento"]["id"],
            "intencion": intencion_confirmada,
            "resultado": resultado,
        }

    return ejecutar_en_transaccion(_operacion)



def obtener_contexto_listado_movimientos_caja(limite: int = 100) -> dict[str, Any]:
    """Devuelve contexto de pantalla para listado de movimientos de caja."""
    movimientos = [
        _preparar_movimiento_caja_para_pantalla(movimiento)
        for movimiento in listar_movimientos_caja(limite)
    ]

    return {
        "movimientos_caja": movimientos,
        "cantidad_movimientos_caja": len(movimientos),
    }


def obtener_contexto_detalle_movimiento_caja(movimiento_id: Any) -> dict[str, Any]:
    """Devuelve contexto de pantalla para detalle de movimiento de caja."""
    movimiento = obtener_movimiento_caja_por_id(movimiento_id)

    if movimiento is None:
        raise ValueError("No existe el movimiento de caja informado.")

    movimiento_pantalla = _preparar_movimiento_caja_para_pantalla(movimiento)
    lineas_pantalla = [
        _preparar_linea_movimiento_caja_para_pantalla(linea)
        for linea in movimiento["lineas"]
    ]

    return {
        "movimiento_caja": movimiento_pantalla,
        "lineas_movimiento_caja": lineas_pantalla,
        "cantidad_lineas_movimiento_caja": len(lineas_pantalla),
    }


def _preparar_movimiento_caja_para_pantalla(
    movimiento: dict[str, Any],
) -> dict[str, Any]:
    movimiento_pantalla = dict(movimiento)
    movimiento_pantalla["fecha_argentina"] = _formatear_fecha_iso(movimiento["fecha"])
    movimiento_pantalla["total_contable_argentina"] = _formatear_centavos(
        movimiento["total_contable_centavos"]
    )
    movimiento_pantalla["tipo_movimiento_mostrar"] = movimiento["tipo_movimiento"]
    movimiento_pantalla["estado_mostrar"] = movimiento["estado"].title()
    movimiento_pantalla["estado_badge"] = _badge_estado_movimiento(movimiento["estado"])
    movimiento_pantalla["origen_tipo_mostrar"] = movimiento.get("origen_tipo") or "MANUAL"
    movimiento_pantalla["origen_mostrar"] = _formatear_origen_movimiento(movimiento)
    movimiento_pantalla["asiento_mostrar"] = (
        f"Asiento {movimiento['asiento_id']}"
        if movimiento.get("asiento_id")
        else ""
    )
    movimiento_pantalla["observaciones_mostrar"] = movimiento.get("observaciones") or ""

    return movimiento_pantalla


def _preparar_linea_movimiento_caja_para_pantalla(
    linea: dict[str, Any],
) -> dict[str, Any]:
    linea_pantalla = dict(linea)
    linea_pantalla["medio_operativo_mostrar"] = _unir_codigo_descripcion(
        linea["medio_operativo_codigo"],
        linea.get("medio_operativo_nombre"),
    )
    linea_pantalla["cuenta_contable_mostrar"] = _unir_codigo_descripcion(
        linea["cuenta_contable_codigo"],
        linea.get("cuenta_contable_descripcion"),
    )
    linea_pantalla["fecha_valor_argentina"] = (
        _formatear_fecha_iso(linea["fecha_valor"])
        if linea.get("fecha_valor")
        else ""
    )
    linea_pantalla["referencia_mostrar"] = linea.get("referencia") or ""
    linea_pantalla["detalle_mostrar"] = linea.get("detalle") or ""
    linea_pantalla["importe_nominal_argentina"] = _formatear_centavos(
        linea["importe_nominal_centavos"]
    )
    linea_pantalla["importe_contable_argentina"] = _formatear_centavos(
        linea["importe_contable_centavos"]
    )
    linea_pantalla["cotizacion_mostrar"] = formatear_entero_escala_a_decimal_argentino(
        int(linea["cotizacion_1000000"]),
        6,
    )

    return linea_pantalla


def _formatear_origen_movimiento(movimiento: dict[str, Any]) -> str:
    origen_tipo = movimiento.get("origen_tipo")
    origen_id = movimiento.get("origen_id")

    if origen_tipo and origen_id:
        return f"{origen_tipo} #{origen_id}"

    return "Sin origen"


def _unir_codigo_descripcion(codigo: Any, descripcion: Any) -> str:
    codigo_normalizado = str(codigo or "").strip()
    descripcion_normalizada = str(descripcion or "").strip()

    if codigo_normalizado and descripcion_normalizada:
        return f"{codigo_normalizado} - {descripcion_normalizada}"

    return codigo_normalizado or descripcion_normalizada


def _badge_estado_movimiento(estado: str) -> str:
    if estado == "CONFIRMADO":
        return "text-bg-success"

    if estado == "BORRADOR":
        return "text-bg-warning"

    if estado == "ANULADO":
        return "text-bg-danger"

    return "text-bg-secondary"


def _formatear_fecha_iso(fecha_iso: str) -> str:
    return formatear_fecha_iso_a_argentina(fecha_iso)


def _extraer_lineas_caja_desde_formulario(formulario: Any, fecha_default_iso: str) -> list[dict[str, Any]]:
    lineas_por_indice: dict[int, dict[str, Any]] = {}

    for clave in _iterar_claves_formulario(formulario):
        match = _LINEA_FORM_RE.match(str(clave))
        if not match:
            continue

        indice = int(match.group(1))
        campo = match.group(2)
        lineas_por_indice.setdefault(indice, {})[campo] = _obtener_valor_formulario(formulario, clave)

    lineas = []
    for orden, indice in enumerate(sorted(lineas_por_indice), start=1):
        linea = lineas_por_indice[indice]
        codigo_medio = (
            _normalizar_texto_opcional(linea.get("medio_operativo_codigo"))
            or _normalizar_texto_opcional(linea.get("medio_operativo_codigo_select"))
        )
        importe_texto = _normalizar_texto_opcional(linea.get("importe"))

        if not codigo_medio and not importe_texto:
            continue

        if not codigo_medio:
            raise ValueError(f"El medio operativo de la linea {orden} es obligatorio.")

        importe_centavos = _normalizar_importe_argentino(
            importe_texto,
            f"El importe de la linea {orden} debe respetar formato argentino 9.999,99.",
        )
        fecha_valor = _normalizar_fecha_argentina_opcional(
            linea.get("fecha_valor"),
            fecha_default_iso,
        )

        lineas.append(
            {
                "medio_operativo_codigo": codigo_medio,
                "importe_centavos": importe_centavos,
                "fecha_valor": fecha_valor,
                "referencia": _normalizar_texto_opcional(linea.get("referencia")),
                "detalle": _normalizar_texto_opcional(linea.get("detalle")),
                "orden": orden,
            }
        )

    if not lineas:
        raise ValueError("Debe cargar al menos una linea de caja.")

    return lineas


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



def _titulo_formulario_caja(tipo_movimiento: str, origen_tipo: str | None) -> str:
    if _es_cobro_cliente(tipo_movimiento, origen_tipo):
        return "Confirmar cobro"

    if tipo_movimiento == "INGRESO":
        return "Registrar ingreso de dinero"

    if tipo_movimiento == "EGRESO":
        return "Registrar salida de dinero"

    return "Registrar movimiento de caja"


def _descripcion_formulario_caja(tipo_movimiento: str, origen_tipo: str | None) -> str:
    if _es_cobro_cliente(tipo_movimiento, origen_tipo):
        return "Completá cómo se recibió el dinero. Al confirmar se registra el cobro."

    if tipo_movimiento == "INGRESO":
        return "Completá cómo ingresó el dinero y confirmá el registro."

    if tipo_movimiento == "EGRESO":
        return "Completá cómo salió el dinero y confirmá el registro."

    return "Completá los datos de caja y confirmá el registro."


def _resumen_operacion_formulario_caja(
    tipo_movimiento: str,
    origen_tipo: str | None,
    origen_descripcion: str | None,
) -> str:
    origen_mostrar = origen_descripcion or "sin origen informado"

    if _es_cobro_cliente(tipo_movimiento, origen_tipo):
        return f"Vas a registrar un cobro generado desde {origen_mostrar}."

    if tipo_movimiento == "INGRESO":
        return f"Vas a registrar una entrada de dinero desde {origen_mostrar}."

    if tipo_movimiento == "EGRESO":
        return f"Vas a registrar una salida de dinero desde {origen_mostrar}."

    return f"Vas a registrar un movimiento de caja desde {origen_mostrar}."


def _total_label_formulario_caja(tipo_movimiento: str, origen_tipo: str | None) -> str:
    if _es_cobro_cliente(tipo_movimiento, origen_tipo):
        return "Importe a cobrar"

    if tipo_movimiento == "INGRESO":
        return "Importe a ingresar"

    if tipo_movimiento == "EGRESO":
        return "Importe a pagar"

    return "Importe a registrar"


def _medios_titulo_formulario_caja(tipo_movimiento: str) -> str:
    if tipo_movimiento == "EGRESO":
        return "Medios de pago"

    return "Medios de cobro"


def _medios_subtitulo_formulario_caja(tipo_movimiento: str) -> str:
    if tipo_movimiento == "EGRESO":
        return "Indicá con qué medio se pagó."

    return "Indicá cómo se recibió el dinero."


def _confirmar_label_formulario_caja(tipo_movimiento: str, origen_tipo: str | None) -> str:
    if _es_cobro_cliente(tipo_movimiento, origen_tipo):
        return "Confirmar cobro"

    if tipo_movimiento == "EGRESO":
        return "Confirmar pago"

    return "Confirmar ingreso"


def _tipo_movimiento_mostrar(tipo_movimiento: str) -> str:
    if tipo_movimiento == "INGRESO":
        return "Ingreso de dinero"

    if tipo_movimiento == "EGRESO":
        return "Salida de dinero"

    return tipo_movimiento.title()


def _estado_formulario_mostrar(estado: str) -> str:
    if estado == _ESTADO_PENDIENTE:
        return "Pendiente de confirmar"

    if estado == "BORRADOR":
        return "Sin confirmar"

    return estado.title()


def _origen_tipo_formulario_mostrar(origen_tipo: str | None) -> str:
    origen_normalizado = str(origen_tipo or "").strip().upper()

    if origen_normalizado == _ORIGEN_RECIBO_CLIENTE:
        return "Cobro de cliente"

    if origen_normalizado:
        return origen_normalizado.replace("_", " ").title()

    return "Manual"


def _ayuda_confirmacion_formulario_caja(tipo_movimiento: str, origen_tipo: str | None) -> str:
    if _es_cobro_cliente(tipo_movimiento, origen_tipo):
        return "Al confirmar se registra el cobro, el movimiento de caja, la cuenta corriente y el asiento contable."

    return "Al confirmar se registra el movimiento de caja y sus impactos asociados."


def _es_cobro_cliente(tipo_movimiento: str, origen_tipo: str | None) -> bool:
    return (
        tipo_movimiento == "INGRESO"
        and str(origen_tipo or "").strip().upper() == _ORIGEN_RECIBO_CLIENTE
    )

def _armar_concepto(origen_descripcion: str | None) -> str:
    if origen_descripcion:
        return f"Movimiento de caja generado desde {origen_descripcion}."

    return ""


def _fecha_argentina_desde_payload(payload: dict[str, Any]) -> str:
    datos_cobranza = payload.get("datos_cobranza")
    if not isinstance(datos_cobranza, dict):
        return date.today().strftime("%d/%m/%Y")

    fecha_iso = str(datos_cobranza.get("fecha") or "").strip()
    if len(fecha_iso) == 10 and fecha_iso[4] == "-" and fecha_iso[7] == "-":
        return f"{fecha_iso[8:10]}/{fecha_iso[5:7]}/{fecha_iso[0:4]}"

    return date.today().strftime("%d/%m/%Y")


def _iterar_claves_formulario(formulario: Any) -> list[str]:
    if formulario is None:
        return []

    if hasattr(formulario, "keys"):
        return list(formulario.keys())

    return []


def _obtener_arg(args: Any, clave: str, default: Any = "") -> Any:
    if hasattr(args, "get"):
        return args.get(clave, default)

    return default


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


def _normalizar_tipo_movimiento(valor: Any) -> str:
    tipo = str(valor or "").strip().upper()

    if tipo not in _TIPOS_MOVIMIENTO_VALIDOS:
        return _TIPO_MOVIMIENTO_DEFAULT

    return tipo


def _normalizar_fecha_argentina(valor: Any, mensaje: str) -> str:
    texto = str(valor or "").strip()
    if not texto:
        raise ValueError(mensaje)

    try:
        return normalizar_fecha_argentina_a_iso(texto)
    except ValueError as exc:
        raise ValueError(mensaje) from exc


def _normalizar_fecha_argentina_opcional(valor: Any, default_iso: str) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return default_iso

    return _normalizar_fecha_argentina(texto, "La fecha valor debe ser valida.")


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


def _normalizar_entero_no_negativo(valor: Any) -> int:
    try:
        entero = int(str(valor or "0").strip())
    except ValueError:
        return 0

    return max(entero, 0)


def _normalizar_entero_positivo_opcional(valor: Any) -> int | None:
    texto = str(valor or "").strip()
    if not texto:
        return None

    entero = _validar_entero_positivo(texto, "El id debe ser positivo.")
    return entero


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


def _normalizar_texto_opcional(valor: Any) -> str | None:
    texto = str(valor or "").strip()
    return texto or None


def _copiar_dict(valor: Any, mensaje: str) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise ValueError(mensaje)

    return dict(valor)


def _copiar_lista(valor: Any, mensaje: str) -> list[dict[str, Any]]:
    if not isinstance(valor, list):
        raise ValueError(mensaje)

    return [dict(item) for item in valor]


def _formatear_centavos(valor: Any) -> str:
    return formatear_entero_escala_a_decimal_argentino(int(valor or 0), 2)
