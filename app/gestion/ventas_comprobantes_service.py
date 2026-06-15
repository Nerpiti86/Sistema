import re
from typing import Any

from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
)
from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_automatico_confirmado,
)
from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_por_fecha,
)
from app.gestion.articulos_venta_repository import obtener_articulo_venta_por_id
from app.gestion.clientes_repository import (
    obtener_cliente_por_id,
    validar_cliente_activo,
)
from app.gestion.clientes_cuenta_corriente_service import (
    crear_movimiento_debe_cliente,
    crear_movimiento_haber_cliente,
)
from app.gestion.ventas_comprobantes_repository import (
    crear_venta_comprobante,
    listar_ventas_comprobantes,
    marcar_venta_comprobante_confirmado,
    obtener_venta_comprobante_por_id,
)

_TIPOS_COMPROBANTE_VALIDOS = {"FACTURA", "NOTA_DEBITO", "NOTA_CREDITO"}
_TIPOS_COMPROBANTE_DEBE_CLIENTE = {"FACTURA", "NOTA_DEBITO"}
_TIPO_ORIGEN_VENTA_COMPROBANTE = "VENTA_COMPROBANTE"
_MONEDA_CONTABLE = "ARS"
_ESCALA_COTIZACION_CONTABLE = 1_000_000
_PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PATRON_MONEDA = re.compile(r"^[A-Z]{3}$")
_ESCALA_CANTIDAD = 1_000_000


def listar_comprobantes_venta() -> list[dict[str, Any]]:
    """
    Devuelve comprobantes de venta sin calcular cobranza ni saldo.

    La lectura de deuda pertenece a cuenta corriente y aplicaciones.
    """
    return listar_ventas_comprobantes()


def obtener_comprobante_venta(comprobante_id: Any) -> dict[str, Any]:
    """Devuelve un comprobante de venta existente o informa error funcional."""
    comprobante = obtener_venta_comprobante_por_id(comprobante_id)

    if comprobante is None:
        raise ValueError("No existe el comprobante de venta informado.")

    return comprobante


def obtener_contexto_listado_comprobantes_venta() -> dict[str, Any]:
    """
    Devuelve contexto de pantalla para listado de comprobantes de venta.

    Solo prepara datos de presentacion. No calcula cobranza ni saldo.
    """
    comprobantes = [
        _preparar_comprobante_venta_para_pantalla(comprobante)
        for comprobante in listar_comprobantes_venta()
    ]

    return {
        "comprobantes_venta": comprobantes,
        "cantidad_comprobantes_venta": len(comprobantes),
    }


def obtener_contexto_detalle_comprobante_venta(
    comprobante_id: Any,
) -> dict[str, Any]:
    """
    Devuelve contexto de pantalla para detalle de comprobante de venta.

    La lectura muestra documento, renglones e impactos ya asociados.
    """
    comprobante = obtener_comprobante_venta(comprobante_id)
    comprobante_pantalla = _preparar_comprobante_venta_para_pantalla(comprobante)
    detalles_pantalla = [
        _preparar_detalle_comprobante_venta_para_pantalla(detalle)
        for detalle in comprobante.get("detalles", [])
    ]

    return {
        "comprobante_venta": comprobante_pantalla,
        "detalles_comprobante_venta": detalles_pantalla,
        "cantidad_detalles_comprobante_venta": len(detalles_pantalla),
    }


def _preparar_comprobante_venta_para_pantalla(
    comprobante: dict[str, Any],
) -> dict[str, Any]:
    comprobante_pantalla = dict(comprobante)
    comprobante_pantalla["fecha_argentina"] = _formatear_fecha_iso_opcional(
        comprobante.get("fecha")
    )
    comprobante_pantalla["fecha_vencimiento_argentina"] = _formatear_fecha_iso_opcional(
        comprobante.get("fecha_vencimiento")
    )
    comprobante_pantalla["subtotal_argentina"] = _formatear_centavos(
        comprobante.get("subtotal_centavos", 0)
    )
    comprobante_pantalla["descuento_argentina"] = _formatear_centavos(
        comprobante.get("descuento_centavos", 0)
    )
    comprobante_pantalla["recargo_argentina"] = _formatear_centavos(
        comprobante.get("recargo_centavos", 0)
    )
    comprobante_pantalla["iva_argentina"] = _formatear_centavos(
        comprobante.get("iva_centavos", 0)
    )
    comprobante_pantalla["total_argentina"] = _formatear_centavos(
        comprobante.get("total_centavos", 0)
    )

    return comprobante_pantalla


def _preparar_detalle_comprobante_venta_para_pantalla(
    detalle: dict[str, Any],
) -> dict[str, Any]:
    detalle_pantalla = dict(detalle)
    detalle_pantalla["precio_unitario_argentina"] = _formatear_centavos(
        detalle.get("precio_unitario_centavos", 0)
    )
    detalle_pantalla["subtotal_argentina"] = _formatear_centavos(
        detalle.get("subtotal_centavos", 0)
    )
    detalle_pantalla["descuento_argentina"] = _formatear_centavos(
        detalle.get("descuento_centavos", 0)
    )
    detalle_pantalla["iva_argentina"] = _formatear_centavos(
        detalle.get("iva_centavos", 0)
    )
    detalle_pantalla["total_linea_argentina"] = _formatear_centavos(
        detalle.get("total_linea_centavos", 0)
    )

    return detalle_pantalla


def _formatear_fecha_iso_opcional(fecha: Any) -> str:
    fecha_normalizada = str(fecha or "").strip()

    if not fecha_normalizada:
        return ""

    return formatear_fecha_iso_a_argentina(fecha_normalizada)


def _formatear_centavos(valor: Any) -> str:
    return formatear_entero_escala_a_decimal_argentino(int(valor or 0), 2)


def crear_borrador_comprobante_venta(
    datos_comprobante: dict[str, Any],
    detalles: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Crea un comprobante comercial de venta en BORRADOR.

    No confirma, no impacta cuenta corriente, no genera asiento y no mueve fondos.
    """
    datos_base = _normalizar_datos_base_comprobante(datos_comprobante)
    cliente = _obtener_cliente_activo(datos_base["cliente_id"])
    detalles_normalizados = _normalizar_detalles_comprobante(
        detalles,
        datos_base["moneda_codigo"],
    )
    importes = _calcular_importes_comprobante(datos_base, detalles_normalizados)

    datos_repository = {
        "cliente_id": cliente["id"],
        "fecha": datos_base["fecha"],
        "fecha_vencimiento": datos_base["fecha_vencimiento"],
        "tipo_comprobante": datos_base["tipo_comprobante"],
        "letra": datos_base["letra"],
        "punto_venta": datos_base["punto_venta"],
        "numero": datos_base["numero"],
        "moneda_codigo": datos_base["moneda_codigo"],
        "cotizacion_centavos": datos_base["cotizacion_centavos"],
        "subtotal_centavos": importes["subtotal_centavos"],
        "descuento_centavos": importes["descuento_centavos"],
        "recargo_centavos": importes["recargo_centavos"],
        "iva_centavos": importes["iva_centavos"],
        "total_centavos": importes["total_centavos"],
        "estado": "BORRADOR",
        "asiento_id": None,
        "observaciones": datos_base["observaciones"],
    }

    return crear_venta_comprobante(datos_repository, detalles_normalizados)


def confirmar_comprobante_venta(comprobante_id: Any) -> dict[str, Any]:
    """
    Confirma un comprobante de venta sin IVA.

    Genera asiento contable, genera movimiento confirmado de cuenta corriente y
    luego marca el comprobante comercial como CONFIRMADO. No mueve fondos.
    """
    comprobante = obtener_comprobante_venta(comprobante_id)
    _validar_comprobante_confirmable(comprobante)

    cliente = _obtener_cliente_activo(comprobante["cliente_id"])
    cuenta_deudores_codigo = _obtener_cuenta_deudores_cliente(cliente)
    ejercicio = _obtener_ejercicio_para_confirmacion(comprobante["fecha"])
    descripcion = _descripcion_confirmacion_venta(comprobante)

    asiento = crear_asiento_contable_automatico_confirmado(
        {
            "ejercicio_id": ejercicio["id"],
            "fecha": comprobante["fecha"],
            "descripcion": descripcion,
            "tipo": "AJUSTE",
            "cotizacion_tipo": "CIERRE",
        },
        _armar_detalles_asiento_confirmacion(
            comprobante,
            cuenta_deudores_codigo,
            descripcion,
        ),
    )

    movimiento_cuenta_corriente = _crear_movimiento_cuenta_corriente_confirmacion(
        comprobante,
        asiento["id"],
        descripcion,
    )

    comprobante_confirmado = marcar_venta_comprobante_confirmado(
        comprobante["id"],
        asiento["id"],
    )

    return {
        "comprobante": comprobante_confirmado,
        "asiento": asiento,
        "movimiento_cuenta_corriente": movimiento_cuenta_corriente,
    }


def _validar_comprobante_confirmable(comprobante: dict[str, Any]) -> None:
    if comprobante["estado"] != "BORRADOR":
        raise ValueError("Solo se puede confirmar un comprobante en BORRADOR.")

    if comprobante["moneda_codigo"] != _MONEDA_CONTABLE:
        raise ValueError("Solo se pueden confirmar comprobantes en ARS en esta etapa.")

    if int(comprobante["iva_centavos"]) != 0:
        raise ValueError("No se puede confirmar una venta con IVA en esta etapa.")

    if int(comprobante["recargo_centavos"]) != 0:
        raise ValueError(
            "No se puede confirmar una venta con recargo global sin cuenta contable."
        )

    if int(comprobante["total_centavos"]) <= 0:
        raise ValueError("El total del comprobante debe ser positivo para confirmar.")

    detalles = list(comprobante.get("detalles") or [])

    if not detalles:
        raise ValueError("El comprobante de venta debe tener detalle para confirmar.")

    subtotal_detalles = sum(int(detalle["subtotal_centavos"]) for detalle in detalles)
    descuento_detalles = sum(int(detalle["descuento_centavos"]) for detalle in detalles)
    iva_detalles = sum(int(detalle["iva_centavos"]) for detalle in detalles)
    total_detalles = sum(int(detalle["total_linea_centavos"]) for detalle in detalles)

    if subtotal_detalles != int(comprobante["subtotal_centavos"]):
        raise ValueError("El subtotal del comprobante no coincide con sus renglones.")

    if descuento_detalles != int(comprobante["descuento_centavos"]):
        raise ValueError(
            "No se puede confirmar una venta con descuento global sin cuenta contable."
        )

    if iva_detalles != 0:
        raise ValueError("No se puede confirmar una venta con IVA en esta etapa.")

    if total_detalles != int(comprobante["total_centavos"]):
        raise ValueError("El total del comprobante no coincide con sus renglones.")

    for indice, detalle in enumerate(detalles, start=1):
        if int(detalle["total_linea_centavos"]) <= 0:
            raise ValueError(f"El renglon {indice} debe tener importe positivo.")

        if not _normalizar_texto_opcional(detalle.get("cuenta_ingreso_codigo")):
            raise ValueError(f"El renglon {indice} no tiene cuenta de ingreso.")


def _obtener_cuenta_deudores_cliente(cliente: dict[str, Any]) -> str:
    return _validar_texto_obligatorio(
        cliente.get("cuenta_deudores_ventas_codigo"),
        "El cliente no tiene cuenta de deudores por ventas configurada.",
    )


def _obtener_ejercicio_para_confirmacion(fecha: str) -> dict[str, Any]:
    ejercicio = obtener_ejercicio_contable_por_fecha(fecha)

    if ejercicio is None:
        raise ValueError("No existe ejercicio contable para la fecha de la venta.")

    if ejercicio["estado"] != "ABIERTO":
        raise ValueError("El ejercicio contable de la venta no esta abierto.")

    if int(ejercicio["bloqueado"]) == 1:
        raise ValueError("El ejercicio contable de la venta esta bloqueado.")

    return ejercicio


def _descripcion_confirmacion_venta(comprobante: dict[str, Any]) -> str:
    return (
        f"Venta {comprobante['tipo_comprobante']} "
        f"{comprobante['numero_formateado']}"
    )


def _armar_detalles_asiento_confirmacion(
    comprobante: dict[str, Any],
    cuenta_deudores_codigo: str,
    descripcion: str,
) -> list[dict[str, Any]]:
    es_nota_credito = comprobante["tipo_comprobante"] == "NOTA_CREDITO"
    total_centavos = int(comprobante["total_centavos"])
    detalles_asiento: list[dict[str, Any]] = []

    detalles_asiento.append(
        _crear_renglon_asiento_confirmacion(
            cuenta_deudores_codigo,
            descripcion,
            debe_centavos=0 if es_nota_credito else total_centavos,
            haber_centavos=total_centavos if es_nota_credito else 0,
        )
    )

    for detalle in comprobante["detalles"]:
        importe_linea = int(detalle["total_linea_centavos"])
        cuenta_ingreso_codigo = _validar_texto_obligatorio(
            detalle.get("cuenta_ingreso_codigo"),
            "El renglon no tiene cuenta de ingreso.",
        )

        detalles_asiento.append(
            _crear_renglon_asiento_confirmacion(
                cuenta_ingreso_codigo,
                str(detalle["descripcion"]),
                debe_centavos=importe_linea if es_nota_credito else 0,
                haber_centavos=0 if es_nota_credito else importe_linea,
            )
        )

    return detalles_asiento


def _crear_renglon_asiento_confirmacion(
    cuenta_contable_codigo: str,
    descripcion: str,
    debe_centavos: int,
    haber_centavos: int,
) -> dict[str, Any]:
    return {
        "cuenta_contable_codigo": cuenta_contable_codigo,
        "descripcion": descripcion,
        "moneda_codigo": _MONEDA_CONTABLE,
        "cotizacion_1000000": _ESCALA_COTIZACION_CONTABLE,
        "nominal_debe_centavos": debe_centavos,
        "nominal_haber_centavos": haber_centavos,
        "debe_centavos": debe_centavos,
        "haber_centavos": haber_centavos,
    }


def _crear_movimiento_cuenta_corriente_confirmacion(
    comprobante: dict[str, Any],
    asiento_id: int,
    descripcion: str,
) -> dict[str, Any]:
    datos_movimiento = {
        "cliente_id": comprobante["cliente_id"],
        "fecha": comprobante["fecha"],
        "tipo_movimiento": comprobante["tipo_comprobante"],
        "descripcion": descripcion,
        "moneda_codigo": comprobante["moneda_codigo"],
        "estado": "CONFIRMADO",
        "origen_tipo": _TIPO_ORIGEN_VENTA_COMPROBANTE,
        "origen_id": comprobante["id"],
        "asiento_id": asiento_id,
        "importe_centavos": comprobante["total_centavos"],
    }

    if comprobante["tipo_comprobante"] in _TIPOS_COMPROBANTE_DEBE_CLIENTE:
        return crear_movimiento_debe_cliente(datos_movimiento)

    return crear_movimiento_haber_cliente(datos_movimiento)


def _obtener_cliente_activo(cliente_id: int) -> dict[str, Any]:
    validar_cliente_activo(cliente_id)
    cliente = obtener_cliente_por_id(cliente_id)

    if cliente is None:
        raise ValueError("El cliente no existe o no esta activo.")

    if not cliente.get("esta_activo"):
        raise ValueError("El cliente no existe o no esta activo.")

    return cliente


def _normalizar_datos_base_comprobante(
    datos_comprobante: dict[str, Any],
) -> dict[str, Any]:
    estado_informado = str(datos_comprobante.get("estado", "BORRADOR") or "").strip()

    if estado_informado and estado_informado.upper() != "BORRADOR":
        raise ValueError("El service solo puede crear comprobantes en BORRADOR.")

    tipo_comprobante = _validar_opcion(
        datos_comprobante.get("tipo_comprobante"),
        _TIPOS_COMPROBANTE_VALIDOS,
        "El tipo de comprobante es invalido.",
    )

    return {
        "cliente_id": _validar_entero_positivo(
            datos_comprobante.get("cliente_id"),
            "El cliente es obligatorio.",
        ),
        "fecha": _validar_fecha_iso(
            datos_comprobante.get("fecha"),
            "La fecha del comprobante es obligatoria.",
        ),
        "fecha_vencimiento": _validar_fecha_iso_opcional(
            datos_comprobante.get("fecha_vencimiento"),
            "La fecha de vencimiento debe tener formato YYYY-MM-DD.",
        ),
        "tipo_comprobante": tipo_comprobante,
        "letra": _validar_texto_obligatorio(
            datos_comprobante.get("letra", "X"),
            "La letra del comprobante es obligatoria.",
        ).upper(),
        "punto_venta": _validar_entero_no_negativo(
            datos_comprobante.get("punto_venta", 0),
            "El punto de venta debe ser un entero no negativo.",
        ),
        "numero": _validar_entero_no_negativo(
            datos_comprobante.get("numero", 0),
            "El numero del comprobante debe ser un entero no negativo.",
        ),
        "moneda_codigo": _validar_codigo_moneda(
            datos_comprobante.get("moneda_codigo", "ARS"),
            "La moneda del comprobante es obligatoria.",
        ),
        "cotizacion_centavos": _validar_entero_positivo(
            datos_comprobante.get("cotizacion_centavos", 100),
            "La cotizacion debe ser positiva.",
        ),
        "descuento_centavos": _validar_entero_no_negativo(
            datos_comprobante.get("descuento_centavos", 0),
            "El descuento global debe ser un entero no negativo.",
        ),
        "recargo_centavos": _validar_entero_no_negativo(
            datos_comprobante.get("recargo_centavos", 0),
            "El recargo global debe ser un entero no negativo.",
        ),
        "observaciones": _normalizar_texto_opcional(
            datos_comprobante.get("observaciones")
        ),
    }


def _normalizar_detalles_comprobante(
    detalles: list[dict[str, Any]],
    moneda_codigo: str,
) -> list[dict[str, Any]]:
    if not detalles:
        raise ValueError("El comprobante de venta debe tener al menos un renglon.")

    return [
        _normalizar_detalle_comprobante(detalle, indice, moneda_codigo)
        for indice, detalle in enumerate(detalles, 1)
    ]


def _normalizar_detalle_comprobante(
    detalle: dict[str, Any],
    indice: int,
    moneda_codigo: str,
) -> dict[str, Any]:
    articulo_id = _validar_entero_positivo(
        detalle.get("articulo_venta_id"),
        f"El articulo del renglon {indice} es obligatorio.",
    )
    articulo = obtener_articulo_venta_por_id(articulo_id)

    if articulo is None:
        raise ValueError(f"No existe el articulo del renglon {indice}.")

    if not articulo.get("esta_activo"):
        raise ValueError(f"El articulo del renglon {indice} no esta activo.")

    if articulo.get("moneda_codigo") != moneda_codigo:
        raise ValueError(
            f"La moneda del articulo del renglon {indice} no coincide "
            "con la moneda del comprobante."
        )

    cuenta_ingreso_codigo = _normalizar_texto_opcional(
        articulo.get("cuenta_ingreso_codigo")
    )

    if cuenta_ingreso_codigo is None:
        raise ValueError(
            f"El articulo del renglon {indice} no tiene cuenta de ingreso configurada."
        )

    descripcion = _normalizar_texto_opcional(detalle.get("descripcion"))

    if descripcion is None:
        descripcion = _validar_texto_obligatorio(
            articulo.get("nombre"),
            f"La descripcion del renglon {indice} es obligatoria.",
        )

    cantidad_1000000 = _validar_entero_positivo(
        detalle.get("cantidad_1000000", _ESCALA_CANTIDAD),
        f"La cantidad del renglon {indice} debe ser positiva.",
    )
    precio_unitario_centavos = _validar_entero_no_negativo(
        detalle.get(
            "precio_unitario_centavos",
            articulo.get("precio_unitario_sugerido_centavos", 0),
        ),
        f"El precio unitario del renglon {indice} debe ser no negativo.",
    )
    descuento_centavos = _validar_entero_no_negativo(
        detalle.get("descuento_centavos", 0),
        f"El descuento del renglon {indice} debe ser no negativo.",
    )
    iva_centavos = _validar_entero_no_negativo(
        detalle.get("iva_centavos", 0),
        f"El IVA del renglon {indice} debe ser no negativo.",
    )

    if iva_centavos != 0:
        raise ValueError(
            "El IVA de ventas todavia no esta habilitado. "
            "Debe resolverse por condicion fiscal antes de permitirlo."
        )

    orden = _validar_entero_no_negativo(
        detalle.get("orden", indice),
        f"El orden del renglon {indice} debe ser no negativo.",
    )
    observaciones = _normalizar_texto_opcional(detalle.get("observaciones"))
    subtotal_centavos = _calcular_subtotal_linea(
        precio_unitario_centavos,
        cantidad_1000000,
    )

    if descuento_centavos > subtotal_centavos:
        raise ValueError(f"El descuento del renglon {indice} supera el subtotal.")

    total_linea_centavos = subtotal_centavos - descuento_centavos + iva_centavos

    return {
        "articulo_venta_id": articulo["id"],
        "descripcion": descripcion,
        "cantidad_1000000": cantidad_1000000,
        "precio_unitario_centavos": precio_unitario_centavos,
        "descuento_centavos": descuento_centavos,
        "subtotal_centavos": subtotal_centavos,
        "iva_centavos": iva_centavos,
        "total_linea_centavos": total_linea_centavos,
        "cuenta_ingreso_codigo": cuenta_ingreso_codigo,
        "orden": orden,
        "observaciones": observaciones,
    }


def _calcular_importes_comprobante(
    datos_base: dict[str, Any],
    detalles: list[dict[str, Any]],
) -> dict[str, int]:
    subtotal_centavos = sum(detalle["subtotal_centavos"] for detalle in detalles)
    descuentos_linea_centavos = sum(
        detalle["descuento_centavos"] for detalle in detalles
    )
    iva_centavos = sum(detalle["iva_centavos"] for detalle in detalles)
    descuento_global_centavos = datos_base["descuento_centavos"]
    descuento_total_centavos = descuentos_linea_centavos + descuento_global_centavos
    recargo_centavos = datos_base["recargo_centavos"]

    if descuento_total_centavos > subtotal_centavos:
        raise ValueError("El descuento total supera el subtotal del comprobante.")

    total_centavos = (
        subtotal_centavos
        - descuento_total_centavos
        + recargo_centavos
        + iva_centavos
    )

    return {
        "subtotal_centavos": subtotal_centavos,
        "descuento_centavos": descuento_total_centavos,
        "recargo_centavos": recargo_centavos,
        "iva_centavos": iva_centavos,
        "total_centavos": total_centavos,
    }


def _calcular_subtotal_linea(
    precio_unitario_centavos: int,
    cantidad_1000000: int,
) -> int:
    numerador = precio_unitario_centavos * cantidad_1000000

    return (numerador + (_ESCALA_CANTIDAD // 2)) // _ESCALA_CANTIDAD


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


def _validar_fecha_iso_opcional(valor: Any, mensaje: str) -> str | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return _validar_fecha_iso(valor_normalizado, mensaje)
