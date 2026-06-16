import re
from typing import Any

from app.shared.transacciones_repository import ejecutar_en_transaccion
from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
    normalizar_decimal_argentino_a_entero_escala,
    normalizar_fecha_argentina_a_iso,
)
from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_automatico_confirmado,
    formatear_numero_asiento_contable,
    obtener_asiento_contable,
)
from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_por_fecha,
)
from app.gestion.articulos_venta_repository import (
    listar_articulos_venta,
    obtener_articulo_venta_por_id,
)
from app.gestion.clientes_repository import (
    listar_clientes_activos,
    obtener_cliente_por_id,
    validar_cliente_activo,
)
from app.gestion.clientes_cuenta_corriente_service import (
    crear_movimiento_debe_cliente,
    crear_movimiento_haber_cliente,
    obtener_contexto_cuenta_corriente_cliente,
)
from app.gestion.ventas_comprobantes_repository import (
    crear_asociacion_comprobante_venta as crear_asociacion_comprobante_venta_repository,
    crear_venta_comprobante,
    listar_ventas_comprobantes,
    marcar_venta_comprobante_confirmado,
    obtener_asociacion_comprobante_venta as obtener_asociacion_comprobante_venta_repository,
    obtener_venta_comprobante_por_id,
    obtener_proximo_numero_venta_comprobante,
)
from app.shared.catalogos_fiscales_repository import (
    listar_catalogo_fiscal_activo,
    validar_item_catalogo_fiscal_activo,
)

_TIPOS_COMPROBANTE_VALIDOS = {"FACTURA", "NOTA_DEBITO", "NOTA_CREDITO"}
_TIPOS_COMPROBANTE_DEBE_CLIENTE = {"FACTURA", "NOTA_DEBITO"}
_TIPOS_COMPROBANTE_FISCALES_VENTA = {
    "011": "FACTURA",
    "012": "NOTA_DEBITO",
    "013": "NOTA_CREDITO",
}
_LETRAS_COMPROBANTE_FISCALES_VENTA = {
    "011": "C",
    "012": "C",
    "013": "C",
}
_TIPOS_COMPROBANTE_CODIGO_POR_OPERATIVO = {
    valor: codigo for codigo, valor in _TIPOS_COMPROBANTE_FISCALES_VENTA.items()
}
_TIPO_ORIGEN_VENTA_COMPROBANTE = "VENTA_COMPROBANTE"
_MONEDA_CONTABLE = "ARS"
_ESCALA_COTIZACION_CONTABLE = 1_000_000
_PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PATRON_MONEDA = re.compile(r"^[A-Z]{3}$")
_ESCALA_CANTIDAD = 1_000_000
_ESCALA_PORCENTAJE = 10_000
_ESCALA_PORCENTAJE_CALCULO = 100 * _ESCALA_PORCENTAJE
_UNIDAD_MEDIDA_DEFAULT = "7"
_PUNTO_VENTA_DEFAULT = 1
_TIPO_BONIFICACION_PORCENTAJE = "1"
_TIPO_BONIFICACION_MONTO = "2"


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


def obtener_asociacion_comprobante_venta(
    comprobante_id: Any,
) -> dict[str, Any] | None:
    """Devuelve la relacion comercial del comprobante, si existe."""
    return obtener_asociacion_comprobante_venta_repository(comprobante_id)


def asociar_comprobante_venta_a_factura(
    comprobante_id: Any,
    factura_id: Any,
) -> dict[str, Any]:
    """
    Vincula una ND/NC en BORRADOR con la FC confirmada que modifica.
    """
    comprobante = obtener_comprobante_venta(comprobante_id)
    factura = obtener_comprobante_venta(factura_id)

    if comprobante["tipo_comprobante"] not in {"NOTA_DEBITO", "NOTA_CREDITO"}:
        raise ValueError("Solo ND o NC pueden modificar una FC.")

    if comprobante["estado"] != "BORRADOR":
        raise ValueError("La ND/NC debe estar en BORRADOR para asociarla.")

    if factura["tipo_comprobante"] != "FACTURA":
        raise ValueError("El comprobante asociado debe ser una FC.")

    if factura["estado"] != "CONFIRMADO":
        raise ValueError("La FC asociada debe estar CONFIRMADA.")

    if int(comprobante["cliente_id"]) != int(factura["cliente_id"]):
        raise ValueError("La FC asociada debe pertenecer al mismo cliente.")

    return crear_asociacion_comprobante_venta_repository(
        {
            "comprobante_id": comprobante["id"],
            "comprobante_asociado_id": factura["id"],
            "tipo_relacion": "MODIFICA",
        }
    )


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

    movimiento_cuenta_corriente = (
        _obtener_movimiento_cuenta_corriente_comprobante_para_pantalla(comprobante)
    )
    asociacion_comprobante = obtener_asociacion_comprobante_venta(comprobante["id"])

    return {
        "comprobante_venta": comprobante_pantalla,
        "detalles_comprobante_venta": detalles_pantalla,
        "cantidad_detalles_comprobante_venta": len(detalles_pantalla),
        "movimiento_cuenta_corriente_venta": movimiento_cuenta_corriente,
        "asociacion_comprobante_venta": asociacion_comprobante,
    }


def _obtener_movimiento_cuenta_corriente_comprobante_para_pantalla(
    comprobante: dict[str, Any],
) -> dict[str, Any] | None:
    contexto_cuenta_corriente = obtener_contexto_cuenta_corriente_cliente(
        comprobante["cliente_id"]
    )

    for movimiento in contexto_cuenta_corriente["movimientos"]:
        if movimiento.get("origen_tipo") != _TIPO_ORIGEN_VENTA_COMPROBANTE:
            continue

        if int(movimiento.get("origen_id") or 0) != int(comprobante["id"]):
            continue

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

    return None


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
    _agregar_asiento_contable_para_pantalla(comprobante_pantalla)

    return comprobante_pantalla


def _agregar_asiento_contable_para_pantalla(
    comprobante_pantalla: dict[str, Any],
) -> None:
    """
    Agrega etiqueta visual de asiento contable.

    La pantalla de ventas debe mostrar el numero contable del asiento y conservar
    el ID tecnico solo como trazabilidad.
    """
    asiento_id = comprobante_pantalla.get("asiento_id")
    comprobante_pantalla["asiento_numero_mostrar"] = ""
    comprobante_pantalla["asiento_mostrar"] = ""

    if asiento_id is None:
        return

    asiento = obtener_asiento_contable(asiento_id)

    if asiento is None:
        comprobante_pantalla["asiento_mostrar"] = f"ID {asiento_id}"
        return

    numero_asiento = asiento.get("numero_asiento")

    if numero_asiento is None:
        comprobante_pantalla["asiento_mostrar"] = f"Sin numero (ID {asiento_id})"
        return

    numero_asiento_mostrar = formatear_numero_asiento_contable(asiento)
    comprobante_pantalla["asiento_numero_mostrar"] = numero_asiento_mostrar
    comprobante_pantalla["asiento_mostrar"] = f"{numero_asiento_mostrar} (ID {asiento_id})"


def _preparar_detalle_comprobante_venta_para_pantalla(
    detalle: dict[str, Any],
) -> dict[str, Any]:
    detalle_pantalla = dict(detalle)
    detalle_pantalla["precio_unitario_argentina"] = _formatear_centavos(
        detalle.get("precio_unitario_centavos", 0)
    )
    detalle_pantalla["bonificacion_valor_argentina"] = _formatear_bonificacion_valor(
        detalle
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


def _formatear_bonificacion_valor(detalle: dict[str, Any]) -> str:
    tipo_bonificacion_codigo = _normalizar_texto_opcional(
        detalle.get("tipo_bonificacion_codigo")
    )

    if tipo_bonificacion_codigo is None:
        return ""

    if tipo_bonificacion_codigo == _TIPO_BONIFICACION_PORCENTAJE:
        return formatear_entero_escala_a_decimal_argentino(
            int(detalle.get("bonificacion_valor_10000", 0)),
            4,
        )

    return _formatear_centavos(detalle.get("descuento_centavos", 0))


def obtener_contexto_formulario_comprobante_venta(
    comprobante_form: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Devuelve contexto para el formulario de nuevo comprobante de venta.

    El usuario carga los datos y al confirmar se genera venta, asiento y cuenta corriente.
    """
    formulario = _preparar_comprobante_venta_formulario(comprobante_form or {})
    tipo_comprobante, tipo_comprobante_codigo = _resolver_tipo_comprobante_venta(
        formulario.get("tipo_comprobante")
    )
    formulario["tipo_comprobante"] = tipo_comprobante_codigo
    formulario["letra"] = _resolver_letra_comprobante_venta(tipo_comprobante_codigo)
    formulario["punto_venta"] = str(_PUNTO_VENTA_DEFAULT)
    formulario["numero"] = str(
        obtener_proximo_numero_venta_comprobante(
            tipo_comprobante,
            formulario["letra"],
            _PUNTO_VENTA_DEFAULT,
        )
    )
    clientes = listar_clientes_activos()
    articulos_venta = [
        articulo for articulo in listar_articulos_venta() if articulo["esta_activo"]
    ]
    tipos_comprobante_venta = [
        tipo
        for tipo in listar_catalogo_fiscal_activo("tipos_comprobante")
        if tipo["codigo"] in _TIPOS_COMPROBANTE_FISCALES_VENTA
    ]
    unidades_medida = listar_catalogo_fiscal_activo("unidades_medida")
    tipos_bonificacion = listar_catalogo_fiscal_activo("tipos_bonificacion")
    facturas_confirmadas_asociables = _listar_facturas_confirmadas_para_asociacion()

    return {
        "comprobante_form": formulario,
        "clientes": clientes,
        "articulos_venta": articulos_venta,
        "tipos_comprobante_venta": tipos_comprobante_venta,
        "unidades_medida": unidades_medida,
        "tipos_bonificacion": tipos_bonificacion,
        "facturas_confirmadas_asociables": facturas_confirmadas_asociables,
        "cantidad_clientes": len(clientes),
        "cantidad_articulos_venta": len(articulos_venta),
        "cantidad_unidades_medida": len(unidades_medida),
        "cantidad_tipos_bonificacion": len(tipos_bonificacion),
        "cantidad_facturas_confirmadas_asociables": len(facturas_confirmadas_asociables),
    }


def _listar_facturas_confirmadas_para_asociacion() -> list[dict[str, Any]]:
    """Devuelve FC confirmadas disponibles para asociar ND/NC desde pantalla."""
    facturas = []

    for comprobante in listar_comprobantes_venta():
        if comprobante.get("tipo_comprobante") != "FACTURA":
            continue

        if comprobante.get("estado") != "CONFIRMADO":
            continue

        factura = _preparar_comprobante_venta_para_pantalla(comprobante)
        factura["opcion_asociacion"] = (
            f"{factura['numero_formateado']} - "
            f"{factura['fecha_argentina']} - "
            f"{factura['total_argentina']}"
        )
        facturas.append(factura)

    return facturas


def crear_borrador_comprobante_venta_desde_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """
    Crea un comprobante de venta BORRADOR desde pantalla.

    El alta minima carga un solo renglon y no confirma, no cobra ni mueve fondos.
    """
    datos_comprobante, detalle = _normalizar_formulario_borrador_comprobante_venta(
        formulario
    )

    return crear_borrador_comprobante_venta(datos_comprobante, [detalle])


def _preparar_comprobante_venta_formulario(
    comprobante_form: dict[str, Any],
) -> dict[str, Any]:
    formulario = dict(comprobante_form)
    formulario.setdefault("fecha", "")
    formulario.setdefault("fecha_vencimiento", "")
    formulario["fecha"] = _formatear_fecha_formulario_para_pantalla(
        formulario.get("fecha")
    )
    formulario["fecha_vencimiento"] = _formatear_fecha_formulario_para_pantalla(
        formulario.get("fecha_vencimiento")
    )
    formulario.setdefault("tipo_comprobante", "011")
    formulario.setdefault("letra", "C")
    formulario.setdefault("punto_venta", str(_PUNTO_VENTA_DEFAULT))
    formulario.setdefault("numero", "")
    formulario.setdefault("moneda_codigo", _MONEDA_CONTABLE)
    formulario.setdefault("cotizacion_centavos", "100")
    formulario.setdefault("cantidad", "1,00")
    formulario.setdefault("unidad_medida_codigo", _UNIDAD_MEDIDA_DEFAULT)
    formulario.setdefault("precio_unitario_centavos", "")
    formulario.setdefault("tipo_bonificacion_codigo", "")
    formulario.setdefault("bonificacion_valor", "")
    formulario.setdefault("descripcion", "")
    formulario.setdefault("observaciones", "")
    formulario.setdefault("comprobante_asociado_id", "")

    return formulario


def _formatear_fecha_formulario_para_pantalla(valor: Any) -> str:
    fecha_normalizada = str(valor or "").strip()

    if not fecha_normalizada:
        return ""

    if _PATRON_FECHA_ISO.match(fecha_normalizada):
        return _formatear_fecha_iso_opcional(fecha_normalizada)

    return fecha_normalizada


def _normalizar_formulario_borrador_comprobante_venta(
    formulario: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    tipo_comprobante, tipo_comprobante_codigo = _resolver_tipo_comprobante_venta(
        formulario.get("tipo_comprobante")
    )
    moneda_codigo = _validar_codigo_moneda(
        formulario.get("moneda_codigo", _MONEDA_CONTABLE),
        "La moneda del comprobante es obligatoria.",
    )

    if moneda_codigo != _MONEDA_CONTABLE:
        raise ValueError("El alta de comprobantes de venta solo permite ARS en esta etapa.")

    datos_comprobante = {
        "cliente_id": _validar_entero_positivo(
            formulario.get("cliente_id"),
            "El cliente es obligatorio.",
        ),
        "fecha": _validar_fecha_iso(
            formulario.get("fecha"),
            "La fecha del comprobante es obligatoria.",
        ),
        "fecha_vencimiento": _validar_fecha_iso_opcional(
            formulario.get("fecha_vencimiento"),
            "La fecha de vencimiento debe tener formato YYYY-MM-DD.",
        ),
        "tipo_comprobante": tipo_comprobante,
        "tipo_comprobante_codigo": tipo_comprobante_codigo,
        "letra": _resolver_letra_comprobante_venta(tipo_comprobante_codigo),
        "punto_venta": _PUNTO_VENTA_DEFAULT,
        "numero": obtener_proximo_numero_venta_comprobante(
            tipo_comprobante,
            _resolver_letra_comprobante_venta(tipo_comprobante_codigo),
            _PUNTO_VENTA_DEFAULT,
        ),
        "moneda_codigo": moneda_codigo,
        "cotizacion_centavos": _validar_entero_positivo(
            formulario.get("cotizacion_centavos", 100),
            "La cotizacion debe ser positiva.",
        ),
        "observaciones": _normalizar_texto_opcional(formulario.get("observaciones")),
    }

    detalle = {
        "articulo_venta_id": _validar_entero_positivo(
            formulario.get("articulo_venta_id"),
            "El producto o servicio es obligatorio.",
        ),
        "cantidad_1000000": _normalizar_cantidad_formulario_a_1000000(
            formulario.get("cantidad")
        ),
        "unidad_medida_codigo": _normalizar_unidad_medida_codigo(
            formulario.get("unidad_medida_codigo", _UNIDAD_MEDIDA_DEFAULT)
        ),
        "iva_centavos": 0,
        "orden": 1,
    }

    descripcion = _normalizar_texto_opcional(formulario.get("descripcion"))
    if descripcion is not None:
        detalle["descripcion"] = descripcion

    precio_unitario_centavos = _normalizar_precio_unitario_formulario(
        formulario.get("precio_unitario_centavos")
    )
    if precio_unitario_centavos is not None:
        detalle["precio_unitario_centavos"] = precio_unitario_centavos

    tipo_bonificacion_codigo = _normalizar_tipo_bonificacion_codigo_opcional(
        formulario.get("tipo_bonificacion_codigo")
    )
    if tipo_bonificacion_codigo is not None:
        detalle["tipo_bonificacion_codigo"] = tipo_bonificacion_codigo
        detalle["bonificacion_valor_10000"] = _normalizar_bonificacion_valor_formulario(
            tipo_bonificacion_codigo,
            formulario.get("bonificacion_valor"),
        )

    return datos_comprobante, detalle


def _normalizar_cantidad_formulario_a_1000000(valor: Any) -> int:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        raise ValueError("La cantidad del renglon es obligatoria.")

    try:
        cantidad_100 = normalizar_decimal_argentino_a_entero_escala(
            valor_normalizado,
            2,
        )
    except ValueError as exc:
        raise ValueError(
            "La cantidad debe respetar formato argentino 9.999,99."
        ) from exc

    cantidad_1000000 = cantidad_100 * 10_000
    if cantidad_1000000 <= 0:
        raise ValueError("La cantidad del renglon debe ser positiva.")

    return cantidad_1000000


def _normalizar_precio_unitario_formulario(valor: Any) -> int | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    try:
        precio_unitario_centavos = normalizar_decimal_argentino_a_entero_escala(
            valor_normalizado,
            2,
        )
    except ValueError as exc:
        raise ValueError(
            "El precio unitario debe respetar formato argentino 9.999,99."
        ) from exc

    if precio_unitario_centavos < 0:
        raise ValueError("El precio unitario no puede ser negativo.")

    return precio_unitario_centavos


def _normalizar_bonificacion_valor_formulario(
    tipo_bonificacion_codigo: str,
    valor: Any,
) -> int:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return 0

    if tipo_bonificacion_codigo == _TIPO_BONIFICACION_PORCENTAJE:
        escala = 4
        mensaje = "El porcentaje de bonificacion debe respetar formato argentino 99,9999."
    else:
        escala = 2
        mensaje = "El importe de bonificacion debe respetar formato argentino 9.999,99."

    try:
        valor_entero = normalizar_decimal_argentino_a_entero_escala(
            valor_normalizado,
            escala,
        )
    except ValueError as exc:
        raise ValueError(mensaje) from exc

    if valor_entero < 0:
        raise ValueError("La bonificacion del renglon no puede ser negativa.")

    return valor_entero


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
        "tipo_comprobante_codigo": datos_base["tipo_comprobante_codigo"],
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


def crear_y_confirmar_comprobante_venta_desde_formulario(formulario: Any) -> dict[str, Any]:
    """
    Crea y confirma una venta desde el formulario Nuevo comprobante.

    Contrato: el usuario carga los datos y al confirmar se genera la venta,
    el asiento contable y el movimiento de cuenta corriente. Si falla cualquier
    parte, no queda comprobante borrador huerfano.
    """

    def _crear_y_confirmar() -> dict[str, Any]:
        comprobante_borrador = crear_borrador_comprobante_venta_desde_formulario(
            formulario
        )
        asociacion = _asociar_comprobante_modificador_desde_formulario_si_corresponde(
            comprobante_borrador,
            formulario,
        )
        resultado = confirmar_comprobante_venta(comprobante_borrador["id"])

        if asociacion is not None:
            resultado["asociacion_comprobante_venta"] = asociacion

        return resultado

    return ejecutar_en_transaccion(_crear_y_confirmar)


def _asociar_comprobante_modificador_desde_formulario_si_corresponde(
    comprobante_borrador: dict[str, Any],
    formulario: Any,
) -> dict[str, Any] | None:
    if comprobante_borrador["tipo_comprobante"] not in {"NOTA_DEBITO", "NOTA_CREDITO"}:
        return None

    factura_id = _validar_entero_positivo(
        formulario.get("comprobante_asociado_id"),
        "La FC asociada es obligatoria para ND/NC.",
    )

    return asociar_comprobante_venta_a_factura(
        comprobante_borrador["id"],
        factura_id,
    )


def confirmar_comprobante_venta(comprobante_id: Any) -> dict[str, Any]:
    """
    Confirma un comprobante de venta sin IVA.

    Genera asiento contable, genera movimiento confirmado de cuenta corriente y
    luego marca el comprobante comercial como CONFIRMADO. No mueve fondos.

    La confirmacion es transaccional: si falla una parte, no queda impacto
    parcial en ventas, cuenta corriente ni contabilidad.
    """

    def _confirmar_en_transaccion() -> dict[str, Any]:
        comprobante = obtener_comprobante_venta(comprobante_id)
        _validar_comprobante_confirmable(comprobante)

        cliente = _obtener_cliente_activo(comprobante["cliente_id"])
        cuenta_deudores_codigo = _obtener_cuenta_deudores_cliente(cliente)
        ejercicio = _obtener_ejercicio_para_confirmacion(comprobante["fecha"])
        descripcion_asiento = _descripcion_confirmacion_venta(comprobante)
        descripcion_movimiento = _descripcion_movimiento_cuenta_corriente_confirmacion(
            comprobante
        )

        asiento = crear_asiento_contable_automatico_confirmado(
            {
                "ejercicio_id": ejercicio["id"],
                "fecha": comprobante["fecha"],
                "descripcion": descripcion_asiento,
                "tipo": "VENTA",
                "cotizacion_tipo": "CIERRE",
            },
            _armar_detalles_asiento_confirmacion(
                comprobante,
                cuenta_deudores_codigo,
            ),
        )

        movimiento_cuenta_corriente = _crear_movimiento_cuenta_corriente_confirmacion(
            comprobante,
            asiento["id"],
            descripcion_movimiento,
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

    return ejecutar_en_transaccion(_confirmar_en_transaccion)


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
    return _descripcion_comprobante_sujeto(comprobante)


def _descripcion_movimiento_cuenta_corriente_confirmacion(
    comprobante: dict[str, Any],
) -> str:
    return str(comprobante["numero_formateado"])


def _descripcion_linea_deudores_confirmacion(comprobante: dict[str, Any]) -> str:
    return _descripcion_comprobante_sujeto(comprobante)


def _descripcion_linea_resultado_confirmacion(comprobante: dict[str, Any]) -> str:
    return _descripcion_comprobante_sujeto(comprobante)


def _descripcion_comprobante_sujeto(comprobante: dict[str, Any]) -> str:
    return (
        f"Comprobante: {comprobante['numero_formateado']} | "
        f"Sujeto: {_descripcion_cliente_comprobante(comprobante)}"
    )


def _descripcion_cliente_comprobante(comprobante: dict[str, Any]) -> str:
    return _validar_texto_obligatorio(
        comprobante.get("cliente_razon_social"),
        "El comprobante no tiene cliente para describir el asiento.",
    )

def _armar_detalles_asiento_confirmacion(
    comprobante: dict[str, Any],
    cuenta_deudores_codigo: str,
) -> list[dict[str, Any]]:
    es_nota_credito = comprobante["tipo_comprobante"] == "NOTA_CREDITO"
    total_centavos = int(comprobante["total_centavos"])
    detalles_asiento: list[dict[str, Any]] = []

    detalles_asiento.append(
        _crear_renglon_asiento_confirmacion(
            cuenta_deudores_codigo,
            _descripcion_linea_deudores_confirmacion(comprobante),
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
                _descripcion_linea_resultado_confirmacion(comprobante),
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

    tipo_comprobante, tipo_comprobante_codigo = _resolver_tipo_comprobante_venta(
        datos_comprobante.get("tipo_comprobante_codigo")
        or datos_comprobante.get("tipo_comprobante")
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
        "tipo_comprobante_codigo": tipo_comprobante_codigo,
        "letra": _resolver_letra_comprobante_venta(tipo_comprobante_codigo),
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
    unidad_medida_codigo = _normalizar_unidad_medida_codigo(
        detalle.get("unidad_medida_codigo", _UNIDAD_MEDIDA_DEFAULT)
    )
    precio_unitario_centavos = _validar_entero_no_negativo(
        detalle.get(
            "precio_unitario_centavos",
            articulo.get("precio_unitario_sugerido_centavos", 0),
        ),
        f"El precio unitario del renglon {indice} debe ser no negativo.",
    )
    tipo_bonificacion_codigo = _normalizar_tipo_bonificacion_codigo_opcional(
        detalle.get("tipo_bonificacion_codigo")
    )
    bonificacion_valor_10000 = _validar_entero_no_negativo(
        detalle.get("bonificacion_valor_10000", 0),
        f"El valor de bonificacion del renglon {indice} debe ser no negativo.",
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
    descuento_centavos = _calcular_importe_bonificacion_linea(
        subtotal_centavos,
        tipo_bonificacion_codigo,
        bonificacion_valor_10000,
        detalle.get("descuento_centavos", 0),
    )

    if descuento_centavos > subtotal_centavos:
        raise ValueError(f"El descuento del renglon {indice} supera el subtotal.")

    total_linea_centavos = subtotal_centavos - descuento_centavos + iva_centavos

    return {
        "articulo_venta_id": articulo["id"],
        "descripcion": descripcion,
        "cantidad_1000000": cantidad_1000000,
        "unidad_medida_codigo": unidad_medida_codigo,
        "precio_unitario_centavos": precio_unitario_centavos,
        "tipo_bonificacion_codigo": tipo_bonificacion_codigo,
        "bonificacion_valor_10000": bonificacion_valor_10000,
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


def _calcular_importe_bonificacion_linea(
    subtotal_centavos: int,
    tipo_bonificacion_codigo: str | None,
    bonificacion_valor_10000: int,
    descuento_legacy: Any,
) -> int:
    if tipo_bonificacion_codigo is None:
        return _validar_entero_no_negativo(
            descuento_legacy,
            "El descuento del renglon debe ser no negativo.",
        )

    if tipo_bonificacion_codigo == _TIPO_BONIFICACION_PORCENTAJE:
        return (
            subtotal_centavos * bonificacion_valor_10000
            + (_ESCALA_PORCENTAJE_CALCULO // 2)
        ) // _ESCALA_PORCENTAJE_CALCULO

    return bonificacion_valor_10000


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


def _normalizar_unidad_medida_codigo(valor: Any) -> str:
    codigo = _validar_codigo_catalogo(valor, "La unidad de medida del renglon es obligatoria.")
    validar_item_catalogo_fiscal_activo("unidades_medida", codigo)
    return codigo


def _normalizar_tipo_bonificacion_codigo_opcional(valor: Any) -> str | None:
    codigo = _normalizar_texto_opcional(valor)

    if codigo is None:
        return None

    codigo = _validar_codigo_catalogo(codigo, "El tipo de bonificacion del renglon es invalido.")
    validar_item_catalogo_fiscal_activo("tipos_bonificacion", codigo)
    return codigo


def _validar_codigo_catalogo(valor: Any, mensaje: str) -> str:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado or len(valor_normalizado) > 3 or not valor_normalizado.isdigit():
        raise ValueError(mensaje)

    return valor_normalizado


def _resolver_tipo_comprobante_venta(valor: Any) -> tuple[str, str]:
    valor_normalizado = str(valor or "").strip().upper()

    if valor_normalizado in _TIPOS_COMPROBANTE_FISCALES_VENTA:
        return (
            _TIPOS_COMPROBANTE_FISCALES_VENTA[valor_normalizado],
            valor_normalizado,
        )

    if valor_normalizado in _TIPOS_COMPROBANTE_VALIDOS:
        return (
            valor_normalizado,
            _TIPOS_COMPROBANTE_CODIGO_POR_OPERATIVO[valor_normalizado],
        )

    raise ValueError("El tipo de comprobante es invalido.")


def _resolver_letra_comprobante_venta(tipo_comprobante_codigo: str) -> str:
    try:
        return _LETRAS_COMPROBANTE_FISCALES_VENTA[tipo_comprobante_codigo]
    except KeyError as exc:
        raise ValueError("No existe letra fiscal definida para el tipo de comprobante.") from exc


def _validar_codigo_moneda(valor: Any, mensaje: str) -> str:
    valor_normalizado = str(valor or "").strip().upper()

    if not _PATRON_MONEDA.match(valor_normalizado):
        raise ValueError(mensaje)

    return valor_normalizado


def _validar_fecha_iso(valor: Any, mensaje: str) -> str:
    valor_normalizado = str(valor or "").strip()

    if "/" in valor_normalizado:
        try:
            valor_normalizado = normalizar_fecha_argentina_a_iso(valor_normalizado)
        except ValueError as exc:
            raise ValueError(mensaje) from exc

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
