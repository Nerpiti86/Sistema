from datetime import date
from typing import Any

from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
    normalizar_fecha_argentina_a_iso,
)
from app.gestion.clientes_cuenta_corriente_repository import (
    calcular_saldo_cliente_cuenta_corriente,
    crear_movimiento_cliente_cuenta_corriente,
    listar_movimientos_cliente_cuenta_corriente,
    obtener_movimiento_cliente_cuenta_corriente_por_id,
)
from app.gestion.clientes_repository import obtener_cliente_por_id, validar_cliente_activo

_TIPOS_DEBE_VALIDOS = {"FACTURA", "NOTA_DEBITO", "AJUSTE"}
_TIPOS_HABER_VALIDOS = {"COBRANZA", "ANTICIPO", "NOTA_CREDITO", "AJUSTE"}
_ESTADOS_MOVIMIENTO_VALIDOS = {"BORRADOR", "CONFIRMADO", "ANULADO"}


def crear_movimiento_debe_cliente(
    datos_movimiento: dict[str, Any],
) -> dict[str, Any]:
    """
    Crea un movimiento al DEBE de la cuenta corriente de clientes.

    El service aplica reglas funcionales y delega persistencia al repository.
    """
    datos_base = _normalizar_datos_base_movimiento(datos_movimiento)
    tipo_movimiento = _validar_opcion(
        datos_base["tipo_movimiento"],
        _TIPOS_DEBE_VALIDOS,
        "El tipo de movimiento no corresponde al DEBE de clientes.",
    )
    importe_centavos = _validar_importe_positivo(
        datos_movimiento.get("importe_centavos", datos_movimiento.get("debe_centavos")),
    )

    validar_cliente_activo(datos_base["cliente_id"])

    return crear_movimiento_cliente_cuenta_corriente(
        {
            **datos_base,
            "tipo_movimiento": tipo_movimiento,
            "debe_centavos": importe_centavos,
            "haber_centavos": 0,
        }
    )


def crear_movimiento_haber_cliente(
    datos_movimiento: dict[str, Any],
) -> dict[str, Any]:
    """
    Crea un movimiento al HABER de la cuenta corriente de clientes.

    Sirve para cobranzas, anticipos, notas de credito y ajustes al HABER.
    """
    datos_base = _normalizar_datos_base_movimiento(datos_movimiento)
    tipo_movimiento = _validar_opcion(
        datos_base["tipo_movimiento"],
        _TIPOS_HABER_VALIDOS,
        "El tipo de movimiento no corresponde al HABER de clientes.",
    )
    importe_centavos = _validar_importe_positivo(
        datos_movimiento.get("importe_centavos", datos_movimiento.get("haber_centavos")),
    )

    validar_cliente_activo(datos_base["cliente_id"])

    return crear_movimiento_cliente_cuenta_corriente(
        {
            **datos_base,
            "tipo_movimiento": tipo_movimiento,
            "debe_centavos": 0,
            "haber_centavos": importe_centavos,
        }
    )


def obtener_contexto_cuenta_corriente_cliente(
    cliente_id: Any,
    estado: Any = None,
    fecha_desde: Any = None,
    fecha_hasta: Any = None,
) -> dict[str, Any]:
    """
    Devuelve contexto funcional de cuenta corriente de un cliente.

    El saldo devuelto es una lectura calculada, no un dato persistido.
    """
    cliente_id_normalizado = normalizar_id_cliente_cuenta_corriente(cliente_id)
    cliente = obtener_cliente_por_id(cliente_id_normalizado)

    if cliente is None:
        raise ValueError("No existe el cliente informado.")

    estado_normalizado = None
    if estado is not None and str(estado).strip():
        estado_normalizado = _validar_opcion(
            estado,
            _ESTADOS_MOVIMIENTO_VALIDOS,
            "El estado del movimiento es invalido.",
        )

    fecha_desde_normalizada = _normalizar_fecha_iso_opcional(
        fecha_desde,
        "La fecha desde debe tener formato YYYY-MM-DD.",
    )
    fecha_hasta_normalizada = _normalizar_fecha_iso_opcional(
        fecha_hasta,
        "La fecha hasta debe tener formato YYYY-MM-DD.",
    )

    if (
        fecha_desde_normalizada
        and fecha_hasta_normalizada
        and fecha_desde_normalizada > fecha_hasta_normalizada
    ):
        raise ValueError("La fecha desde no puede ser posterior a la fecha hasta.")

    movimientos_todos = listar_movimientos_cliente_cuenta_corriente(
        cliente_id_normalizado,
        estado=estado_normalizado,
    )

    saldo_inicial_centavos = _calcular_saldo_inicial_centavos(
        movimientos_todos,
        fecha_desde_normalizada,
    )
    movimientos_rango = _filtrar_movimientos_por_rango(
        movimientos_todos,
        fecha_desde_normalizada,
        fecha_hasta_normalizada,
    )
    movimientos_pantalla, saldo_final_centavos = (
        _preparar_movimientos_cliente_cuenta_corriente_con_saldo(
            movimientos_rango,
            saldo_inicial_centavos,
        )
    )

    lectura_saldo = calcular_lectura_saldo_cliente(
        cliente_id_normalizado,
        solo_confirmados=True,
    )

    return {
        "cliente": cliente,
        "movimientos": movimientos_pantalla,
        "cantidad_movimientos": len(movimientos_pantalla),
        "lectura_saldo": _preparar_lectura_saldo_cliente_para_pantalla(lectura_saldo),
        "saldo_inicial": _preparar_saldo_para_pantalla(saldo_inicial_centavos),
        "saldo_final": _preparar_saldo_para_pantalla(saldo_final_centavos),
        "estado_filtro": estado_normalizado,
        "filtros": {
            "fecha_desde": _formatear_fecha_iso_opcional(fecha_desde_normalizada),
            "fecha_hasta": _formatear_fecha_iso_opcional(fecha_hasta_normalizada),
            "estado": estado_normalizado or "",
        },
        "saldo_inicial_etiqueta": _preparar_etiqueta_saldo_inicial(
            fecha_desde_normalizada
        ),
    }


def _calcular_saldo_inicial_centavos(
    movimientos: list[dict[str, Any]],
    fecha_desde: str | None,
) -> int:
    if not fecha_desde:
        return 0

    saldo = 0
    for movimiento in movimientos:
        if str(movimiento.get("fecha") or "") >= fecha_desde:
            continue
        saldo += _importe_saldo_movimiento(movimiento)

    return saldo


def _filtrar_movimientos_por_rango(
    movimientos: list[dict[str, Any]],
    fecha_desde: str | None,
    fecha_hasta: str | None,
) -> list[dict[str, Any]]:
    movimientos_filtrados = []

    for movimiento in movimientos:
        fecha_movimiento = str(movimiento.get("fecha") or "")

        if fecha_desde and fecha_movimiento < fecha_desde:
            continue

        if fecha_hasta and fecha_movimiento > fecha_hasta:
            continue

        movimientos_filtrados.append(movimiento)

    return movimientos_filtrados


def _preparar_movimientos_cliente_cuenta_corriente_con_saldo(
    movimientos: list[dict[str, Any]],
    saldo_inicial_centavos: int,
) -> tuple[list[dict[str, Any]], int]:
    saldo_actual = int(saldo_inicial_centavos)
    movimientos_pantalla = []

    for movimiento in movimientos:
        saldo_actual += _importe_saldo_movimiento(movimiento)
        movimientos_pantalla.append(
            _preparar_movimiento_cliente_cuenta_corriente_para_pantalla(
                movimiento,
                saldo_actual,
            )
        )

    return movimientos_pantalla, saldo_actual


def _importe_saldo_movimiento(movimiento: dict[str, Any]) -> int:
    if str(movimiento.get("estado") or "").upper() != "CONFIRMADO":
        return 0

    return int(movimiento.get("debe_centavos") or 0) - int(
        movimiento.get("haber_centavos") or 0
    )


def _preparar_movimiento_cliente_cuenta_corriente_para_pantalla(
    movimiento: dict[str, Any],
    saldo_centavos: int,
) -> dict[str, Any]:
    movimiento_pantalla = dict(movimiento)
    movimiento_pantalla["fecha_argentina"] = _formatear_fecha_iso_opcional(
        movimiento.get("fecha")
    )
    movimiento_pantalla["movimiento_mostrar"] = _mostrar_tipo_movimiento(
        movimiento.get("tipo_movimiento")
    )
    movimiento_pantalla["detalle_mostrar"] = _mostrar_detalle_movimiento(movimiento)
    movimiento_pantalla["debe_argentina"] = _formatear_centavos(
        movimiento.get("debe_centavos", 0)
    )
    movimiento_pantalla["haber_argentina"] = _formatear_centavos(
        movimiento.get("haber_centavos", 0)
    )
    movimiento_pantalla["saldo_centavos"] = saldo_centavos
    movimiento_pantalla["saldo_argentina"] = _formatear_centavos(abs(saldo_centavos))
    movimiento_pantalla["saldo_lado"] = _mostrar_lado_saldo(saldo_centavos)
    movimiento_pantalla["accion_tipo"] = _obtener_accion_tipo_movimiento(movimiento)
    movimiento_pantalla["accion_id"] = _obtener_accion_id_movimiento(movimiento)
    movimiento_pantalla["accion_texto"] = _obtener_accion_texto_movimiento(movimiento)
    return movimiento_pantalla


def _preparar_lectura_saldo_cliente_para_pantalla(
    lectura_saldo: dict[str, int],
) -> dict[str, Any]:
    lectura_pantalla: dict[str, Any] = dict(lectura_saldo)
    saldo_centavos = int(lectura_saldo.get("saldo_centavos", 0))
    lectura_pantalla["total_debe_argentina"] = _formatear_centavos(
        lectura_saldo.get("total_debe_centavos", 0)
    )
    lectura_pantalla["total_haber_argentina"] = _formatear_centavos(
        lectura_saldo.get("total_haber_centavos", 0)
    )
    lectura_pantalla["saldo_argentina"] = _formatear_centavos(abs(saldo_centavos))
    lectura_pantalla["saldo_lado"] = _mostrar_lado_saldo(saldo_centavos)
    return lectura_pantalla


def _preparar_saldo_para_pantalla(saldo_centavos: int) -> dict[str, Any]:
    return {
        "saldo_centavos": saldo_centavos,
        "saldo_argentina": _formatear_centavos(abs(saldo_centavos)),
        "saldo_lado": _mostrar_lado_saldo(saldo_centavos),
    }


def _preparar_etiqueta_saldo_inicial(fecha_desde: str | None) -> str:
    if not fecha_desde:
        return "Saldo inicial"

    return (
        "Saldo inicial acumulado antes del "
        f"{formatear_fecha_iso_a_argentina(fecha_desde)}"
    )


def _mostrar_tipo_movimiento(tipo_movimiento: Any) -> str:
    codigo = str(tipo_movimiento or "").strip().upper()
    mapa = {
        "FACTURA": "FC",
        "COBRANZA": "Cobranza",
        "ANTICIPO": "Anticipo",
        "NOTA_CREDITO": "NC",
        "NOTA_DEBITO": "ND",
        "AJUSTE": "Ajuste",
    }
    return mapa.get(codigo, codigo.replace("_", " ").title())


def _mostrar_detalle_movimiento(movimiento: dict[str, Any]) -> str:
    descripcion = str(movimiento.get("descripcion") or "").strip()
    tipo = str(movimiento.get("tipo_movimiento") or "").strip().upper()
    prefijo_corto = _mostrar_tipo_movimiento(tipo)

    prefijos = [
        f"Venta {tipo} ",
        f"Venta {prefijo_corto} ",
        "Venta FACTURA ",
        "Venta NOTA_CREDITO ",
        "Venta NOTA_DEBITO ",
        "Venta ",
        "Cobranza ",
    ]

    detalle = descripcion
    for prefijo in prefijos:
        if detalle.startswith(prefijo):
            detalle = detalle[len(prefijo):].strip()
            break

    if tipo in {"FACTURA", "NOTA_DEBITO", "NOTA_CREDITO"}:
        if detalle.startswith(f"{prefijo_corto} "):
            return detalle
        return f"{prefijo_corto} {detalle}".strip()

    return detalle


def _mostrar_lado_saldo(saldo_centavos: int) -> str:
    if int(saldo_centavos) < 0:
        return "ACREEDOR"

    return "DEUDOR"


def _obtener_accion_tipo_movimiento(movimiento: dict[str, Any]) -> str:
    origen_tipo = str(movimiento.get("origen_tipo") or "").strip().upper()

    if origen_tipo == "VENTA_COMPROBANTE" and movimiento.get("origen_id"):
        return "COMPROBANTE_VENTA"

    if movimiento.get("asiento_id"):
        return "ASIENTO"

    return ""


def _obtener_accion_id_movimiento(movimiento: dict[str, Any]) -> int | None:
    accion_tipo = _obtener_accion_tipo_movimiento(movimiento)

    if accion_tipo == "COMPROBANTE_VENTA":
        return int(movimiento["origen_id"])

    if accion_tipo == "ASIENTO":
        return int(movimiento["asiento_id"])

    return None


def _obtener_accion_texto_movimiento(movimiento: dict[str, Any]) -> str:
    accion_tipo = _obtener_accion_tipo_movimiento(movimiento)

    if accion_tipo == "COMPROBANTE_VENTA":
        return "Ver comprobante"

    if accion_tipo == "ASIENTO":
        return "Ver asiento"

    return ""


def _formatear_centavos(valor: Any) -> str:
    return formatear_entero_escala_a_decimal_argentino(int(valor or 0), 2)


def _formatear_fecha_iso_opcional(fecha: Any) -> str:
    fecha_normalizada = str(fecha or "").strip()

    if not fecha_normalizada:
        return ""

    return formatear_fecha_iso_a_argentina(fecha_normalizada)


def _normalizar_fecha_iso_opcional(fecha: Any, mensaje_error: str) -> str | None:
    fecha_normalizada = str(fecha or "").strip()

    if not fecha_normalizada:
        return None

    if "/" in fecha_normalizada:
        try:
            return normalizar_fecha_argentina_a_iso(fecha_normalizada)
        except ValueError as exc:
            raise ValueError(mensaje_error) from exc

    try:
        date.fromisoformat(fecha_normalizada)
    except ValueError as exc:
        raise ValueError(mensaje_error) from exc

    return fecha_normalizada


def obtener_movimiento_cliente_cuenta_corriente(
    movimiento_id: Any,
) -> dict[str, Any]:
    """Devuelve un movimiento existente o informa error funcional."""
    movimiento = obtener_movimiento_cliente_cuenta_corriente_por_id(movimiento_id)

    if movimiento is None:
        raise ValueError("No existe el movimiento de cuenta corriente informado.")

    return movimiento


def calcular_lectura_saldo_cliente(
    cliente_id: Any,
    solo_confirmados: bool = True,
) -> dict[str, int]:
    """
    Devuelve lectura calculada DEBE - HABER.

    No persiste saldo y no interpreta el resultado como dato propio del modelo.
    """
    cliente_id_normalizado = normalizar_id_cliente_cuenta_corriente(cliente_id)
    cliente = obtener_cliente_por_id(cliente_id_normalizado)

    if cliente is None:
        raise ValueError("No existe el cliente informado.")

    return calcular_saldo_cliente_cuenta_corriente(
        cliente_id_normalizado,
        solo_confirmados=bool(solo_confirmados),
    )


def normalizar_id_cliente_cuenta_corriente(cliente_id: Any) -> int:
    """Normaliza id de cliente para operaciones de cuenta corriente."""
    try:
        cliente_id_normalizado = int(str(cliente_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del cliente debe ser numerico.") from exc

    if cliente_id_normalizado <= 0:
        raise ValueError("El id del cliente debe ser positivo.")

    return cliente_id_normalizado


def _normalizar_datos_base_movimiento(
    datos_movimiento: dict[str, Any],
) -> dict[str, Any]:
    cliente_id = normalizar_id_cliente_cuenta_corriente(
        datos_movimiento.get("cliente_id"),
    )
    fecha = _validar_texto_obligatorio(
        datos_movimiento.get("fecha"),
        "La fecha del movimiento es obligatoria.",
    )
    tipo_movimiento = _validar_texto_obligatorio(
        datos_movimiento.get("tipo_movimiento"),
        "El tipo de movimiento es obligatorio.",
    ).upper()
    descripcion = _validar_texto_obligatorio(
        datos_movimiento.get("descripcion"),
        "La descripcion del movimiento es obligatoria.",
    )
    moneda_codigo = str(datos_movimiento.get("moneda_codigo", "ARS") or "").strip().upper()
    estado = _validar_opcion(
        datos_movimiento.get("estado", "BORRADOR"),
        _ESTADOS_MOVIMIENTO_VALIDOS,
        "El estado del movimiento es invalido.",
    )

    origen_tipo = _normalizar_texto_opcional(datos_movimiento.get("origen_tipo"))
    if origen_tipo is not None:
        origen_tipo = origen_tipo.upper()

    origen_id = _normalizar_entero_positivo_opcional(datos_movimiento.get("origen_id"))
    asiento_id = _normalizar_entero_positivo_opcional(datos_movimiento.get("asiento_id"))

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
        "estado": estado,
        "origen_tipo": origen_tipo,
        "origen_id": origen_id,
        "asiento_id": asiento_id,
    }


def _validar_importe_positivo(valor: Any) -> int:
    if isinstance(valor, bool):
        raise ValueError("El importe debe ser un entero positivo.")

    try:
        importe_centavos = int(str(valor or "").strip())
    except ValueError as exc:
        raise ValueError("El importe debe ser un entero positivo.") from exc

    if importe_centavos <= 0:
        raise ValueError("El importe debe ser un entero positivo.")

    return importe_centavos


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


def _normalizar_entero_positivo_opcional(valor: Any) -> int | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    try:
        valor_entero = int(valor_normalizado)
    except ValueError as exc:
        raise ValueError("El id opcional informado debe ser positivo.") from exc

    if valor_entero <= 0:
        raise ValueError("El id opcional informado debe ser positivo.")

    return valor_entero


def _validar_opcion(valor: Any, opciones_validas: set[str], mensaje: str) -> str:
    valor_normalizado = str(valor or "").strip().upper()

    if valor_normalizado not in opciones_validas:
        raise ValueError(mensaje)

    return valor_normalizado
