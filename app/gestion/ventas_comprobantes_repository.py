import re
import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db
from app.shared.transacciones_repository import contexto_escritura

_COLUMNAS_SELECT_VENTAS_COMPROBANTES = """
    ventas_comprobantes.id,
    ventas_comprobantes.cliente_id,
    ventas_comprobantes.fecha,
    ventas_comprobantes.fecha_vencimiento,
    ventas_comprobantes.tipo_comprobante,
    ventas_comprobantes.tipo_comprobante_codigo,
    ventas_comprobantes.letra,
    ventas_comprobantes.punto_venta,
    ventas_comprobantes.numero,
    ventas_comprobantes.moneda_codigo,
    ventas_comprobantes.cotizacion_centavos,
    ventas_comprobantes.subtotal_centavos,
    ventas_comprobantes.descuento_centavos,
    ventas_comprobantes.recargo_centavos,
    ventas_comprobantes.iva_centavos,
    ventas_comprobantes.total_centavos,
    ventas_comprobantes.estado,
    ventas_comprobantes.asiento_id,
    ventas_comprobantes.observaciones,
    ventas_comprobantes.creado_en,
    ventas_comprobantes.actualizado_en,
    ventas_comprobantes.confirmado_en,
    ventas_comprobantes.anulado_en,
    clientes.razon_social AS cliente_razon_social,
    clientes.nombre_fantasia AS cliente_nombre_fantasia,
    tipos_comprobante.descripcion AS tipo_comprobante_descripcion,
    monedas.nombre AS moneda_nombre,
    monedas.simbolo AS moneda_simbolo,
    monedas.decimales AS moneda_decimales
"""

_COLUMNAS_SELECT_VENTAS_DETALLE = """
    ventas_comprobantes_detalle.id,
    ventas_comprobantes_detalle.comprobante_id,
    ventas_comprobantes_detalle.articulo_venta_id,
    ventas_comprobantes_detalle.descripcion,
    ventas_comprobantes_detalle.cantidad_1000000,
    ventas_comprobantes_detalle.unidad_medida_codigo,
    ventas_comprobantes_detalle.precio_unitario_centavos,
    ventas_comprobantes_detalle.tipo_bonificacion_codigo,
    ventas_comprobantes_detalle.bonificacion_valor_10000,
    ventas_comprobantes_detalle.descuento_centavos,
    ventas_comprobantes_detalle.subtotal_centavos,
    ventas_comprobantes_detalle.iva_centavos,
    ventas_comprobantes_detalle.total_linea_centavos,
    ventas_comprobantes_detalle.cuenta_ingreso_codigo,
    ventas_comprobantes_detalle.orden,
    ventas_comprobantes_detalle.observaciones,
    articulos_venta.nombre AS articulo_venta_nombre,
    unidades_medida.descripcion AS unidad_medida_descripcion,
    tipos_bonificacion.descripcion AS tipo_bonificacion_descripcion,
    cuentas_contables.descripcion AS cuenta_ingreso_descripcion
"""

_TIPOS_COMPROBANTE_VALIDOS = {"FACTURA", "NOTA_DEBITO", "NOTA_CREDITO"}
_TIPOS_COMPROBANTE_FISCALES_VALIDOS = {
    "011": "FACTURA",
    "012": "NOTA_DEBITO",
    "013": "NOTA_CREDITO",
}
_LETRAS_COMPROBANTE_FISCALES_VALIDAS = {
    "011": "C",
    "012": "C",
    "013": "C",
}
_TIPOS_COMPROBANTE_OPERATIVOS_POR_CODIGO = {
    valor: codigo for codigo, valor in _TIPOS_COMPROBANTE_FISCALES_VALIDOS.items()
}
_PREFIJOS_NUMERO_COMPROBANTE = {
    "FACTURA": "FC",
    "NOTA_DEBITO": "ND",
    "NOTA_CREDITO": "NC",
}
_ESTADOS_COMPROBANTE_VALIDOS = {"BORRADOR", "CONFIRMADO", "ANULADO"}
_PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PATRON_MONEDA = re.compile(r"^[A-Z]{3}$")


def listar_ventas_comprobantes() -> list[dict[str, Any]]:
    """
    Devuelve comprobantes de venta ordenados para gestion.

    No calcula saldos ni estados de cobranza: eso pertenece a cuenta corriente
    y aplicaciones.
    """
    filas_comprobantes = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_VENTAS_COMPROBANTES}
        FROM ventas_comprobantes
        JOIN clientes
          ON clientes.id = ventas_comprobantes.cliente_id
        LEFT JOIN tipos_comprobante
          ON tipos_comprobante.codigo = ventas_comprobantes.tipo_comprobante_codigo
        JOIN monedas
          ON monedas.codigo = ventas_comprobantes.moneda_codigo
        ORDER BY ventas_comprobantes.fecha DESC,
                 ventas_comprobantes.id DESC
        """
    ).fetchall()

    return [
        _normalizar_fila_comprobante(fila_comprobante)
        for fila_comprobante in filas_comprobantes
    ]


def obtener_proximo_numero_venta_comprobante(
    tipo_comprobante: Any,
    letra: Any,
    punto_venta: Any,
) -> int:
    """Devuelve proximo numero disponible para tipo/letra/punto de venta."""
    tipo_normalizado = str(tipo_comprobante or "").strip().upper()
    if tipo_normalizado in _TIPOS_COMPROBANTE_FISCALES_VALIDOS:
        tipo_comprobante_validado = _TIPOS_COMPROBANTE_FISCALES_VALIDOS[
            tipo_normalizado
        ]
    else:
        tipo_comprobante_validado = _validar_opcion(
            tipo_normalizado,
            _TIPOS_COMPROBANTE_VALIDOS,
            "El tipo de comprobante es invalido.",
        )
    letra_validada = _validar_texto_obligatorio(
        letra,
        "La letra del comprobante es obligatoria.",
    ).upper()
    punto_venta_validado = _validar_entero_positivo(
        punto_venta,
        "El punto de venta debe ser positivo.",
    )

    fila = get_db().execute(
        """
        SELECT COALESCE(MAX(numero), 0) + 1 AS proximo_numero
        FROM ventas_comprobantes
        WHERE tipo_comprobante = ?
          AND letra = ?
          AND punto_venta = ?
          AND numero > 0
        """,
        (tipo_comprobante_validado, letra_validada, punto_venta_validado),
    ).fetchone()

    return int(fila["proximo_numero"])


def obtener_venta_comprobante_por_id(
    comprobante_id: Any,
    incluir_detalles: bool = True,
) -> dict[str, Any] | None:
    """Devuelve un comprobante de venta por id, o None si no existe."""
    comprobante_id_validado = _validar_entero_positivo(
        comprobante_id,
        "El id del comprobante es obligatorio.",
    )

    fila_comprobante = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_VENTAS_COMPROBANTES}
        FROM ventas_comprobantes
        JOIN clientes
          ON clientes.id = ventas_comprobantes.cliente_id
        LEFT JOIN tipos_comprobante
          ON tipos_comprobante.codigo = ventas_comprobantes.tipo_comprobante_codigo
        JOIN monedas
          ON monedas.codigo = ventas_comprobantes.moneda_codigo
        WHERE ventas_comprobantes.id = ?
        LIMIT 1
        """,
        (comprobante_id_validado,),
    ).fetchone()

    if fila_comprobante is None:
        return None

    comprobante = _normalizar_fila_comprobante(fila_comprobante)

    if incluir_detalles:
        comprobante["detalles"] = listar_ventas_comprobantes_detalle(
            comprobante_id_validado
        )
        comprobante["cantidad_detalles"] = len(comprobante["detalles"])

    return comprobante


def listar_ventas_comprobantes_detalle(
    comprobante_id: Any,
) -> list[dict[str, Any]]:
    """Devuelve renglones de un comprobante de venta ordenados."""
    comprobante_id_validado = _validar_entero_positivo(
        comprobante_id,
        "El id del comprobante es obligatorio.",
    )

    filas_detalle = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_VENTAS_DETALLE}
        FROM ventas_comprobantes_detalle
        JOIN articulos_venta
          ON articulos_venta.id = ventas_comprobantes_detalle.articulo_venta_id
        LEFT JOIN unidades_medida
          ON unidades_medida.codigo = ventas_comprobantes_detalle.unidad_medida_codigo
        LEFT JOIN tipos_bonificacion
          ON tipos_bonificacion.codigo = ventas_comprobantes_detalle.tipo_bonificacion_codigo
        JOIN cuentas_contables
          ON cuentas_contables.cuenta = ventas_comprobantes_detalle.cuenta_ingreso_codigo
        WHERE ventas_comprobantes_detalle.comprobante_id = ?
        ORDER BY ventas_comprobantes_detalle.orden,
                 ventas_comprobantes_detalle.id
        """,
        (comprobante_id_validado,),
    ).fetchall()

    return [_normalizar_fila_detalle(fila_detalle) for fila_detalle in filas_detalle]


def crear_asociacion_comprobante_venta(datos_asociacion: dict[str, Any]) -> dict[str, Any]:
    """Inserta la relacion comercial entre una ND/NC y la FC que modifica."""
    datos_validados = _validar_datos_asociacion_comprobante(datos_asociacion)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with contexto_escritura(db):
            cursor = db.execute(
                """
                INSERT INTO ventas_comprobantes_asociaciones (
                    comprobante_id,
                    comprobante_asociado_id,
                    tipo_relacion,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    datos_validados["comprobante_id"],
                    datos_validados["comprobante_asociado_id"],
                    datos_validados["tipo_relacion"],
                    creado_en,
                ),
            )
            asociacion_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "La asociacion de comprobantes de venta es invalida o ya existe."
        ) from exc

    asociacion = obtener_asociacion_comprobante_venta_por_id(asociacion_id)

    if asociacion is None:
        raise RuntimeError("No se pudo recuperar la asociacion creada.")

    return asociacion


def obtener_asociacion_comprobante_venta(
    comprobante_id: Any,
) -> dict[str, Any] | None:
    """Devuelve la asociacion de un comprobante modificador, si existe."""
    comprobante_id_validado = _validar_entero_positivo(
        comprobante_id,
        "El id del comprobante es obligatorio.",
    )

    fila = get_db().execute(
        """
        SELECT
            asociaciones.id,
            asociaciones.comprobante_id,
            asociaciones.comprobante_asociado_id,
            asociaciones.tipo_relacion,
            asociaciones.creado_en,
            comprobante.tipo_comprobante AS comprobante_tipo,
            comprobante.cliente_id AS comprobante_cliente_id,
            comprobante.estado AS comprobante_estado,
            comprobante.letra AS comprobante_letra,
            comprobante.punto_venta AS comprobante_punto_venta,
            comprobante.numero AS comprobante_numero,
            asociado.tipo_comprobante AS asociado_tipo,
            asociado.cliente_id AS asociado_cliente_id,
            asociado.estado AS asociado_estado,
            asociado.letra AS asociado_letra,
            asociado.punto_venta AS asociado_punto_venta,
            asociado.numero AS asociado_numero
        FROM ventas_comprobantes_asociaciones AS asociaciones
        JOIN ventas_comprobantes AS comprobante
          ON comprobante.id = asociaciones.comprobante_id
        JOIN ventas_comprobantes AS asociado
          ON asociado.id = asociaciones.comprobante_asociado_id
        WHERE asociaciones.comprobante_id = ?
        LIMIT 1
        """,
        (comprobante_id_validado,),
    ).fetchone()

    if fila is None:
        return None

    return _normalizar_fila_asociacion_comprobante(fila)


def obtener_asociacion_comprobante_venta_por_id(
    asociacion_id: Any,
) -> dict[str, Any] | None:
    """Devuelve una asociacion por id interno."""
    asociacion_id_validado = _validar_entero_positivo(
        asociacion_id,
        "El id de la asociacion es obligatorio.",
    )

    fila = get_db().execute(
        """
        SELECT
            asociaciones.id,
            asociaciones.comprobante_id,
            asociaciones.comprobante_asociado_id,
            asociaciones.tipo_relacion,
            asociaciones.creado_en,
            comprobante.tipo_comprobante AS comprobante_tipo,
            comprobante.cliente_id AS comprobante_cliente_id,
            comprobante.estado AS comprobante_estado,
            comprobante.letra AS comprobante_letra,
            comprobante.punto_venta AS comprobante_punto_venta,
            comprobante.numero AS comprobante_numero,
            asociado.tipo_comprobante AS asociado_tipo,
            asociado.cliente_id AS asociado_cliente_id,
            asociado.estado AS asociado_estado,
            asociado.letra AS asociado_letra,
            asociado.punto_venta AS asociado_punto_venta,
            asociado.numero AS asociado_numero
        FROM ventas_comprobantes_asociaciones AS asociaciones
        JOIN ventas_comprobantes AS comprobante
          ON comprobante.id = asociaciones.comprobante_id
        JOIN ventas_comprobantes AS asociado
          ON asociado.id = asociaciones.comprobante_asociado_id
        WHERE asociaciones.id = ?
        LIMIT 1
        """,
        (asociacion_id_validado,),
    ).fetchone()

    if fila is None:
        return None

    return _normalizar_fila_asociacion_comprobante(fila)


def crear_venta_comprobante(
    datos_comprobante: dict[str, Any],
    detalles: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Inserta cabecera y detalle de un comprobante de venta.

    Este repository solo persiste el documento comercial. No impacta cuenta
    corriente, fondos ni contabilidad.
    """
    datos_validados = _validar_datos_comprobante(datos_comprobante)
    detalles_validados = _validar_detalles(detalles)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with contexto_escritura(db):
            cursor = db.execute(
                """
                INSERT INTO ventas_comprobantes (
                    cliente_id,
                    fecha,
                    fecha_vencimiento,
                    tipo_comprobante,
                    tipo_comprobante_codigo,
                    letra,
                    punto_venta,
                    numero,
                    moneda_codigo,
                    cotizacion_centavos,
                    subtotal_centavos,
                    descuento_centavos,
                    recargo_centavos,
                    iva_centavos,
                    total_centavos,
                    estado,
                    asiento_id,
                    observaciones,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos_validados["cliente_id"],
                    datos_validados["fecha"],
                    datos_validados["fecha_vencimiento"],
                    datos_validados["tipo_comprobante"],
                    datos_validados["tipo_comprobante_codigo"],
                    datos_validados["letra"],
                    datos_validados["punto_venta"],
                    datos_validados["numero"],
                    datos_validados["moneda_codigo"],
                    datos_validados["cotizacion_centavos"],
                    datos_validados["subtotal_centavos"],
                    datos_validados["descuento_centavos"],
                    datos_validados["recargo_centavos"],
                    datos_validados["iva_centavos"],
                    datos_validados["total_centavos"],
                    datos_validados["estado"],
                    datos_validados["asiento_id"],
                    datos_validados["observaciones"],
                    creado_en,
                ),
            )
            comprobante_id = int(cursor.lastrowid)

            for detalle in detalles_validados:
                db.execute(
                    """
                    INSERT INTO ventas_comprobantes_detalle (
                        comprobante_id,
                        articulo_venta_id,
                        descripcion,
                        cantidad_1000000,
                        unidad_medida_codigo,
                        precio_unitario_centavos,
                        tipo_bonificacion_codigo,
                        bonificacion_valor_10000,
                        descuento_centavos,
                        subtotal_centavos,
                        iva_centavos,
                        total_linea_centavos,
                        cuenta_ingreso_codigo,
                        orden,
                        observaciones
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        comprobante_id,
                        detalle["articulo_venta_id"],
                        detalle["descripcion"],
                        detalle["cantidad_1000000"],
                        detalle["unidad_medida_codigo"],
                        detalle["precio_unitario_centavos"],
                        detalle["tipo_bonificacion_codigo"],
                        detalle["bonificacion_valor_10000"],
                        detalle["descuento_centavos"],
                        detalle["subtotal_centavos"],
                        detalle["iva_centavos"],
                        detalle["total_linea_centavos"],
                        detalle["cuenta_ingreso_codigo"],
                        detalle["orden"],
                        detalle["observaciones"],
                    ),
                )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear el comprobante de venta. Revise cliente, moneda, "
            "articulos, cuentas contables o numeracion duplicada."
        ) from exc

    comprobante = obtener_venta_comprobante_por_id(comprobante_id)

    if comprobante is None:
        raise ValueError("No se pudo recuperar el comprobante de venta creado.")

    return comprobante


def marcar_venta_comprobante_confirmado(
    comprobante_id: Any,
    asiento_id: Any,
) -> dict[str, Any]:
    """
    Marca un comprobante de venta BORRADOR como CONFIRMADO.

    Esta primitiva solo actualiza el documento comercial. La creacion del
    asiento contable y del movimiento de cuenta corriente pertenece al service
    orquestador de confirmacion.
    """
    comprobante_id_validado = _validar_entero_positivo(
        comprobante_id,
        "El id del comprobante es obligatorio.",
    )
    asiento_id_validado = _validar_entero_positivo(
        asiento_id,
        "El id del asiento es obligatorio.",
    )

    comprobante_actual = obtener_venta_comprobante_por_id(
        comprobante_id_validado,
        incluir_detalles=False,
    )

    if comprobante_actual is None:
        raise ValueError("No existe el comprobante de venta informado.")

    if comprobante_actual["estado"] != "BORRADOR":
        raise ValueError("Solo se puede confirmar un comprobante en BORRADOR.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    try:
        with contexto_escritura(db):
            cursor = db.execute(
                """
                UPDATE ventas_comprobantes
                SET
                    estado = ?,
                    asiento_id = ?,
                    actualizado_en = ?,
                    confirmado_en = ?
                WHERE id = ?
                  AND estado = ?
                """,
                (
                    "CONFIRMADO",
                    asiento_id_validado,
                    actualizado_en,
                    actualizado_en,
                    comprobante_id_validado,
                    "BORRADOR",
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo confirmar el comprobante de venta. Revise el asiento asociado."
        ) from exc

    if cursor.rowcount != 1:
        raise ValueError("No se pudo confirmar el comprobante de venta.")

    comprobante_confirmado = obtener_venta_comprobante_por_id(comprobante_id_validado)

    if comprobante_confirmado is None:
        raise ValueError("No se pudo recuperar el comprobante de venta confirmado.")

    return comprobante_confirmado


def _normalizar_fila_comprobante(fila_comprobante) -> dict[str, Any]:
    """Convierte una fila SQLite de ventas_comprobantes en dict explicito."""
    comprobante = dict(fila_comprobante)

    for campo in (
        "id",
        "cliente_id",
        "punto_venta",
        "numero",
        "cotizacion_centavos",
        "subtotal_centavos",
        "descuento_centavos",
        "recargo_centavos",
        "iva_centavos",
        "total_centavos",
    ):
        comprobante[campo] = int(comprobante[campo])

    if comprobante.get("asiento_id") is not None:
        comprobante["asiento_id"] = int(comprobante["asiento_id"])

    if comprobante.get("moneda_decimales") is not None:
        comprobante["moneda_decimales"] = int(comprobante["moneda_decimales"])

    comprobante["esta_borrador"] = comprobante["estado"] == "BORRADOR"
    comprobante["esta_confirmado"] = comprobante["estado"] == "CONFIRMADO"
    comprobante["esta_anulado"] = comprobante["estado"] == "ANULADO"
    comprobante["numero_formateado"] = _formatear_numero_comprobante(comprobante)

    return comprobante


def _normalizar_fila_asociacion_comprobante(fila_asociacion) -> dict[str, Any]:
    asociacion = dict(fila_asociacion)

    for campo in (
        "id",
        "comprobante_id",
        "comprobante_asociado_id",
        "comprobante_cliente_id",
        "comprobante_punto_venta",
        "comprobante_numero",
        "asociado_cliente_id",
        "asociado_punto_venta",
        "asociado_numero",
    ):
        asociacion[campo] = int(asociacion[campo])

    asociacion["comprobante_numero_formateado"] = _formatear_numero_comprobante(
        {
            "tipo_comprobante": asociacion["comprobante_tipo"],
            "letra": asociacion["comprobante_letra"],
            "punto_venta": asociacion["comprobante_punto_venta"],
            "numero": asociacion["comprobante_numero"],
        }
    )
    asociacion["comprobante_asociado_numero_formateado"] = _formatear_numero_comprobante(
        {
            "tipo_comprobante": asociacion["asociado_tipo"],
            "letra": asociacion["asociado_letra"],
            "punto_venta": asociacion["asociado_punto_venta"],
            "numero": asociacion["asociado_numero"],
        }
    )

    return asociacion


def _normalizar_fila_detalle(fila_detalle) -> dict[str, Any]:
    """Convierte una fila SQLite de ventas_comprobantes_detalle en dict explicito."""
    detalle = dict(fila_detalle)

    for campo in (
        "id",
        "comprobante_id",
        "articulo_venta_id",
        "cantidad_1000000",
        "precio_unitario_centavos",
        "bonificacion_valor_10000",
        "descuento_centavos",
        "subtotal_centavos",
        "iva_centavos",
        "total_linea_centavos",
        "orden",
    ):
        detalle[campo] = int(detalle[campo])

    return detalle


def _validar_datos_asociacion_comprobante(
    datos_asociacion: dict[str, Any],
) -> dict[str, Any]:
    comprobante_id = _validar_entero_positivo(
        datos_asociacion.get("comprobante_id"),
        "El comprobante modificador es obligatorio.",
    )
    comprobante_asociado_id = _validar_entero_positivo(
        datos_asociacion.get("comprobante_asociado_id"),
        "El comprobante asociado es obligatorio.",
    )

    if comprobante_id == comprobante_asociado_id:
        raise ValueError("Un comprobante no puede asociarse a si mismo.")

    tipo_relacion = _validar_opcion(
        datos_asociacion.get("tipo_relacion", "MODIFICA"),
        {"MODIFICA"},
        "El tipo de relacion de comprobantes es invalido.",
    )

    return {
        "comprobante_id": comprobante_id,
        "comprobante_asociado_id": comprobante_asociado_id,
        "tipo_relacion": tipo_relacion,
    }


def _validar_datos_comprobante(datos_comprobante: dict[str, Any]) -> dict[str, Any]:
    cliente_id = _validar_entero_positivo(
        datos_comprobante.get("cliente_id"),
        "El cliente es obligatorio.",
    )
    fecha = _validar_fecha_iso(
        datos_comprobante.get("fecha"),
        "La fecha del comprobante es obligatoria.",
    )
    fecha_vencimiento = _validar_fecha_iso_opcional(
        datos_comprobante.get("fecha_vencimiento"),
        "La fecha de vencimiento debe tener formato YYYY-MM-DD.",
    )
    tipo_comprobante = _validar_opcion(
        datos_comprobante.get("tipo_comprobante"),
        _TIPOS_COMPROBANTE_VALIDOS,
        "El tipo de comprobante es invalido.",
    )
    tipo_comprobante_codigo = _validar_tipo_comprobante_codigo(
        datos_comprobante.get("tipo_comprobante_codigo"),
        tipo_comprobante,
    )
    letra = _resolver_letra_comprobante(tipo_comprobante_codigo)
    punto_venta = _validar_entero_no_negativo(
        datos_comprobante.get("punto_venta", 0),
        "El punto de venta debe ser un entero no negativo.",
    )
    numero = _validar_entero_no_negativo(
        datos_comprobante.get("numero", 0),
        "El numero del comprobante debe ser un entero no negativo.",
    )
    moneda_codigo = _validar_codigo_moneda(
        datos_comprobante.get("moneda_codigo", "ARS"),
        "La moneda del comprobante es obligatoria.",
    )
    cotizacion_centavos = _validar_entero_positivo(
        datos_comprobante.get("cotizacion_centavos", 100),
        "La cotizacion debe ser positiva.",
    )
    subtotal_centavos = _validar_entero_no_negativo(
        datos_comprobante.get("subtotal_centavos", 0),
        "El subtotal debe ser un entero no negativo.",
    )
    descuento_centavos = _validar_entero_no_negativo(
        datos_comprobante.get("descuento_centavos", 0),
        "El descuento debe ser un entero no negativo.",
    )
    recargo_centavos = _validar_entero_no_negativo(
        datos_comprobante.get("recargo_centavos", 0),
        "El recargo debe ser un entero no negativo.",
    )
    iva_centavos = _validar_entero_no_negativo(
        datos_comprobante.get("iva_centavos", 0),
        "El IVA debe ser un entero no negativo.",
    )
    total_centavos = _validar_entero_no_negativo(
        datos_comprobante.get("total_centavos", 0),
        "El total debe ser un entero no negativo.",
    )
    estado = _validar_opcion(
        datos_comprobante.get("estado", "BORRADOR"),
        _ESTADOS_COMPROBANTE_VALIDOS,
        "El estado del comprobante es invalido.",
    )
    asiento_id = _validar_entero_positivo_opcional(datos_comprobante.get("asiento_id"))
    observaciones = _normalizar_texto_opcional(datos_comprobante.get("observaciones"))

    total_esperado = (
        subtotal_centavos - descuento_centavos + recargo_centavos + iva_centavos
    )

    if total_centavos != total_esperado:
        raise ValueError("El total del comprobante no coincide con sus importes.")

    return {
        "cliente_id": cliente_id,
        "fecha": fecha,
        "fecha_vencimiento": fecha_vencimiento,
        "tipo_comprobante": tipo_comprobante,
        "tipo_comprobante_codigo": tipo_comprobante_codigo,
        "letra": letra,
        "punto_venta": punto_venta,
        "numero": numero,
        "moneda_codigo": moneda_codigo,
        "cotizacion_centavos": cotizacion_centavos,
        "subtotal_centavos": subtotal_centavos,
        "descuento_centavos": descuento_centavos,
        "recargo_centavos": recargo_centavos,
        "iva_centavos": iva_centavos,
        "total_centavos": total_centavos,
        "estado": estado,
        "asiento_id": asiento_id,
        "observaciones": observaciones,
    }


def _validar_detalles(detalles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not detalles:
        raise ValueError("El comprobante de venta debe tener al menos un renglon.")

    return [_validar_detalle(detalle, indice) for indice, detalle in enumerate(detalles, 1)]


def _validar_detalle(detalle: dict[str, Any], indice: int) -> dict[str, Any]:
    articulo_venta_id = _validar_entero_positivo(
        detalle.get("articulo_venta_id"),
        f"El articulo del renglon {indice} es obligatorio.",
    )
    descripcion = _validar_texto_obligatorio(
        detalle.get("descripcion"),
        f"La descripcion del renglon {indice} es obligatoria.",
    )
    cantidad_1000000 = _validar_entero_positivo(
        detalle.get("cantidad_1000000", 1000000),
        f"La cantidad del renglon {indice} debe ser positiva.",
    )
    unidad_medida_codigo = _validar_codigo_catalogo_opcional(
        detalle.get("unidad_medida_codigo", "7"),
        f"La unidad de medida del renglon {indice} es obligatoria.",
    )
    precio_unitario_centavos = _validar_entero_no_negativo(
        detalle.get("precio_unitario_centavos", 0),
        f"El precio unitario del renglon {indice} debe ser no negativo.",
    )
    tipo_bonificacion_codigo = _validar_codigo_catalogo_opcional(
        detalle.get("tipo_bonificacion_codigo"),
        f"El tipo de bonificacion del renglon {indice} es invalido.",
    )
    bonificacion_valor_10000 = _validar_entero_no_negativo(
        detalle.get("bonificacion_valor_10000", 0),
        f"El valor de bonificacion del renglon {indice} debe ser no negativo.",
    )
    descuento_centavos = _validar_entero_no_negativo(
        detalle.get("descuento_centavos", 0),
        f"El descuento del renglon {indice} debe ser no negativo.",
    )
    subtotal_centavos = _validar_entero_no_negativo(
        detalle.get("subtotal_centavos", 0),
        f"El subtotal del renglon {indice} debe ser no negativo.",
    )
    iva_centavos = _validar_entero_no_negativo(
        detalle.get("iva_centavos", 0),
        f"El IVA del renglon {indice} debe ser no negativo.",
    )
    total_linea_centavos = _validar_entero_no_negativo(
        detalle.get("total_linea_centavos", 0),
        f"El total del renglon {indice} debe ser no negativo.",
    )
    cuenta_ingreso_codigo = _validar_texto_obligatorio(
        detalle.get("cuenta_ingreso_codigo"),
        f"La cuenta de ingreso del renglon {indice} es obligatoria.",
    )
    orden = _validar_entero_no_negativo(
        detalle.get("orden", indice),
        f"El orden del renglon {indice} debe ser no negativo.",
    )
    observaciones = _normalizar_texto_opcional(detalle.get("observaciones"))

    total_esperado = subtotal_centavos - descuento_centavos + iva_centavos

    if total_linea_centavos != total_esperado:
        raise ValueError(f"El total del renglon {indice} no coincide con sus importes.")

    return {
        "articulo_venta_id": articulo_venta_id,
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


def _formatear_numero_comprobante(comprobante: dict[str, Any]) -> str:
    if comprobante["punto_venta"] <= 0 or comprobante["numero"] <= 0:
        return ""

    prefijo = _PREFIJOS_NUMERO_COMPROBANTE.get(
        comprobante["tipo_comprobante"],
        comprobante["tipo_comprobante"],
    )
    return (
        f"{prefijo} {comprobante['letra']} "
        f"{comprobante['punto_venta']:04d}-{comprobante['numero']:08d}"
    )


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


def _validar_entero_positivo_opcional(valor: Any) -> int | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return _validar_entero_positivo(
        valor_normalizado,
        "El id opcional informado debe ser positivo.",
    )


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


def _validar_codigo_catalogo_opcional(valor: Any, mensaje: str) -> str | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    if len(valor_normalizado) > 3 or not valor_normalizado.isdigit():
        raise ValueError(mensaje)

    return valor_normalizado


def _validar_tipo_comprobante_codigo(valor: Any, tipo_operativo: str) -> str:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return _TIPOS_COMPROBANTE_OPERATIVOS_POR_CODIGO[tipo_operativo]

    if valor_normalizado not in _TIPOS_COMPROBANTE_FISCALES_VALIDOS:
        raise ValueError("El codigo fiscal de tipo de comprobante es invalido.")

    if _TIPOS_COMPROBANTE_FISCALES_VALIDOS[valor_normalizado] != tipo_operativo:
        raise ValueError("El codigo fiscal no coincide con el tipo de comprobante.")

    return valor_normalizado


def _resolver_letra_comprobante(tipo_comprobante_codigo: str) -> str:
    try:
        return _LETRAS_COMPROBANTE_FISCALES_VALIDAS[tipo_comprobante_codigo]
    except KeyError as exc:
        raise ValueError("No existe letra fiscal definida para el tipo de comprobante.") from exc


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
