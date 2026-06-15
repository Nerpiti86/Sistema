from typing import Any

from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
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
    if estado is not None:
        estado_normalizado = _validar_opcion(
            estado,
            _ESTADOS_MOVIMIENTO_VALIDOS,
            "El estado del movimiento es invalido.",
        )

    movimientos = listar_movimientos_cliente_cuenta_corriente(
        cliente_id_normalizado,
        estado=estado_normalizado,
    )
    movimientos_pantalla = [
        _preparar_movimiento_cliente_cuenta_corriente_para_pantalla(movimiento)
        for movimiento in movimientos
    ]
    lectura_saldo = calcular_lectura_saldo_cliente(
        cliente_id_normalizado,
        solo_confirmados=True,
    )
    lectura_saldo_pantalla = _preparar_lectura_saldo_cliente_para_pantalla(
        lectura_saldo
    )

    return {
        "cliente": cliente,
        "movimientos": movimientos_pantalla,
        "cantidad_movimientos": len(movimientos_pantalla),
        "lectura_saldo": lectura_saldo_pantalla,
        "estado_filtro": estado_normalizado,
    }


def _preparar_movimiento_cliente_cuenta_corriente_para_pantalla(
    movimiento: dict[str, Any],
) -> dict[str, Any]:
    movimiento_pantalla = dict(movimiento)
    movimiento_pantalla["fecha_argentina"] = _formatear_fecha_iso_opcional(
        movimiento.get("fecha")
    )
    movimiento_pantalla["debe_argentina"] = _formatear_centavos(
        movimiento.get("debe_centavos", 0)
    )
    movimiento_pantalla["haber_argentina"] = _formatear_centavos(
        movimiento.get("haber_centavos", 0)
    )
    movimiento_pantalla["importe_argentina"] = _formatear_centavos(
        movimiento.get("importe_centavos", 0)
    )
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
    lectura_pantalla["saldo_lado"] = "DEUDOR" if saldo_centavos >= 0 else "ACREEDOR"
    return lectura_pantalla


def _formatear_centavos(valor: Any) -> str:
    return formatear_entero_escala_a_decimal_argentino(int(valor or 0), 2)


def _formatear_fecha_iso_opcional(fecha: Any) -> str:
    fecha_normalizada = str(fecha or "").strip()

    if not fecha_normalizada:
        return ""

    return formatear_fecha_iso_a_argentina(fecha_normalizada)


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
