import re
from typing import Any

from app.gestion.articulos_venta_repository import obtener_articulo_venta_por_id
from app.gestion.clientes_repository import (
    obtener_cliente_por_id,
    validar_cliente_activo,
)
from app.gestion.ventas_comprobantes_repository import (
    crear_venta_comprobante,
    listar_ventas_comprobantes,
    obtener_venta_comprobante_por_id,
)

_TIPOS_COMPROBANTE_VALIDOS = {"FACTURA", "NOTA_DEBITO", "NOTA_CREDITO"}
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
