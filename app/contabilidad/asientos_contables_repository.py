import re
import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db
from app.shared.transacciones_repository import contexto_escritura
from app.shared.monedas_repository import validar_moneda_activa

_COLUMNAS_SELECT_ASIENTOS_CONTABLES = """
    id,
    ejercicio_id,
    numero_asiento,
    fecha,
    descripcion,
    estado,
    tipo,
    moneda_origen_codigo,
    moneda_destino_codigo,
    cotizacion_id,
    cotizacion_fecha,
    cotizacion_tipo,
    cotizacion_1000000,
    creado_en,
    actualizado_en,
    confirmado_en,
    anulado_en,
    asiento_reversion_id
"""

_COLUMNAS_SELECT_ASIENTOS_CONTABLES_DETALLE = """
    id,
    asiento_id,
    renglon,
    cuenta_contable_codigo,
    descripcion,
    moneda_codigo,
    cotizacion_id,
    cotizacion_fecha,
    cotizacion_tipo,
    cotizacion_1000000,
    nominal_debe_centavos,
    nominal_haber_centavos,
    debe_centavos,
    haber_centavos
"""

_ESTADOS_ASIENTO_VALIDOS = {"BORRADOR", "CONFIRMADO", "ANULADO"}
_TIPOS_ASIENTO_VALIDOS = {"MANUAL", "AJUSTE", "APERTURA", "CIERRE", "REVERSION", "VENTA"}
_TIPOS_COTIZACION_VALIDOS = {"COMPRA", "VENTA", "CIERRE", "PROMEDIO"}
_PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def crear_asiento_contable(
    datos_asiento: dict[str, Any],
    detalles_asiento: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Inserta cabecera y detalle de un asiento contable puro.

    El repository ejecuta SQL y valida estructura de datos persistibles. Las
    reglas de negocio completas, como balanceo, confirmacion y numeracion, se
    resuelven en service.
    """
    fecha = _validar_fecha_iso(datos_asiento.get("fecha"), "La fecha es obligatoria.")
    descripcion = _validar_texto_obligatorio(
        datos_asiento.get("descripcion"),
        "La descripcion del asiento es obligatoria.",
    )
    ejercicio_id = _validar_entero_positivo(
        datos_asiento.get("ejercicio_id"),
        "El ejercicio contable es obligatorio.",
    )
    numero_asiento = _validar_entero_positivo_opcional(
        datos_asiento.get("numero_asiento")
    )
    estado = _validar_opcion(
        datos_asiento.get("estado", "BORRADOR"),
        _ESTADOS_ASIENTO_VALIDOS,
        "El estado del asiento es invalido.",
    )
    tipo = _validar_opcion(
        datos_asiento.get("tipo", "MANUAL"),
        _TIPOS_ASIENTO_VALIDOS,
        "El tipo de asiento es invalido.",
    )

    moneda_origen_codigo = _validar_codigo_moneda(
        datos_asiento.get("moneda_origen_codigo", "ARS"),
        "La moneda origen es obligatoria.",
    )
    moneda_destino_codigo = _validar_codigo_moneda(
        datos_asiento.get("moneda_destino_codigo", "ARS"),
        "La moneda destino es obligatoria.",
    )

    if moneda_destino_codigo != "ARS":
        raise ValueError("La moneda contable destino debe ser ARS.")

    validar_moneda_activa(moneda_origen_codigo)
    validar_moneda_activa(moneda_destino_codigo)

    cotizacion_id = _validar_entero_positivo_opcional(datos_asiento.get("cotizacion_id"))
    cotizacion_fecha = _validar_fecha_iso(
        datos_asiento.get("cotizacion_fecha", fecha),
        "La fecha de cotizacion es obligatoria.",
    )
    cotizacion_tipo = _validar_opcion(
        datos_asiento.get("cotizacion_tipo", "CIERRE"),
        _TIPOS_COTIZACION_VALIDOS,
        "El tipo de cotizacion es invalido.",
    )
    cotizacion_1000000 = _validar_entero_positivo(
        datos_asiento.get("cotizacion_1000000", 1000000),
        "La cotizacion debe ser un entero positivo.",
    )

    if moneda_origen_codigo == moneda_destino_codigo:
        if cotizacion_1000000 != 1000000:
            raise ValueError("La cotizacion ARS/ARS debe ser 1000000.")
        if cotizacion_id is not None:
            raise ValueError("Un asiento ARS/ARS no debe referenciar cotizacion.")

    asiento_default = {
        "moneda_origen_codigo": moneda_origen_codigo,
        "cotizacion_id": cotizacion_id,
        "cotizacion_fecha": cotizacion_fecha,
        "cotizacion_tipo": cotizacion_tipo,
        "cotizacion_1000000": cotizacion_1000000,
    }

    detalles_validados = _validar_detalles_asiento(detalles_asiento, asiento_default)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    confirmado_en = creado_en if estado == "CONFIRMADO" else None

    db = get_db()

    try:
        with contexto_escritura(db):
            numero_asiento = _resolver_numero_asiento_para_insert(
                db,
                ejercicio_id,
                estado,
                numero_asiento,
            )

            cursor = db.execute(
                """
                INSERT INTO asientos_contables (
                    ejercicio_id,
                    numero_asiento,
                    fecha,
                    descripcion,
                    estado,
                    tipo,
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    cotizacion_id,
                    cotizacion_fecha,
                    cotizacion_tipo,
                    cotizacion_1000000,
                    creado_en,
                    confirmado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ejercicio_id,
                    numero_asiento,
                    fecha,
                    descripcion,
                    estado,
                    tipo,
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    cotizacion_id,
                    cotizacion_fecha,
                    cotizacion_tipo,
                    cotizacion_1000000,
                    creado_en,
                    confirmado_en,
                ),
            )

            asiento_id = int(cursor.lastrowid)

            for detalle in detalles_validados:
                db.execute(
                    """
                    INSERT INTO asientos_contables_detalle (
                        asiento_id,
                        renglon,
                        cuenta_contable_codigo,
                        descripcion,
                        moneda_codigo,
                        cotizacion_id,
                        cotizacion_fecha,
                        cotizacion_tipo,
                        cotizacion_1000000,
                        nominal_debe_centavos,
                        nominal_haber_centavos,
                        debe_centavos,
                        haber_centavos
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asiento_id,
                        detalle["renglon"],
                        detalle["cuenta_contable_codigo"],
                        detalle["descripcion"],
                        detalle["moneda_codigo"],
                        detalle["cotizacion_id"],
                        detalle["cotizacion_fecha"],
                        detalle["cotizacion_tipo"],
                        detalle["cotizacion_1000000"],
                        detalle["nominal_debe_centavos"],
                        detalle["nominal_haber_centavos"],
                        detalle["debe_centavos"],
                        detalle["haber_centavos"],
                    ),
                )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo crear el asiento contable.") from exc

    asiento_creado = obtener_asiento_contable_por_id(asiento_id)

    if asiento_creado is None:
        raise ValueError("No se pudo recuperar el asiento contable creado.")

    return asiento_creado


def _resolver_numero_asiento_para_insert(
    db,
    ejercicio_id: int,
    estado: str,
    numero_asiento: int | None,
) -> int | None:
    """
    Resuelve numero_asiento antes de insertar.

    Los asientos CONFIRMADOS nacen numerados por ejercicio contable.
    Los BORRADOR pueden quedar sin numero hasta que exista circuito de
    confirmacion de asientos manuales.
    """
    if numero_asiento is not None:
        return numero_asiento

    if estado != "CONFIRMADO":
        return None

    fila = db.execute(
        """
        SELECT COALESCE(MAX(numero_asiento), 0) + 1 AS proximo_numero
        FROM asientos_contables
        WHERE ejercicio_id = ?
          AND numero_asiento IS NOT NULL
        """,
        (ejercicio_id,),
    ).fetchone()

    return int(fila["proximo_numero"])


def obtener_asiento_contable_por_id(asiento_id: Any) -> dict[str, Any] | None:
    """Devuelve un asiento contable por id, con su detalle ordenado."""
    asiento_id_validado = _validar_entero_positivo(
        asiento_id,
        "El id del asiento es obligatorio.",
    )

    fila_asiento = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_ASIENTOS_CONTABLES}
        FROM asientos_contables
        WHERE id = ?
        LIMIT 1
        """,
        (asiento_id_validado,),
    ).fetchone()

    if fila_asiento is None:
        return None

    asiento = _normalizar_fila_asiento_contable(fila_asiento)
    asiento["detalles"] = _listar_detalles_por_asiento_id(asiento_id_validado)

    return asiento


def listar_asientos_contables_por_ejercicio(
    ejercicio_id: Any,
    limite: int = 100,
) -> list[dict[str, Any]]:
    """Devuelve cabeceras de asientos de un ejercicio, ordenadas por fecha."""
    ejercicio_id_validado = _validar_entero_positivo(
        ejercicio_id,
        "El ejercicio contable es obligatorio.",
    )
    limite_validado = _validar_limite(limite)

    filas_asientos = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_ASIENTOS_CONTABLES}
        FROM asientos_contables
        WHERE ejercicio_id = ?
        ORDER BY fecha DESC, id DESC
        LIMIT ?
        """,
        (ejercicio_id_validado, limite_validado),
    ).fetchall()

    return [
        _normalizar_fila_asiento_contable(fila_asiento)
        for fila_asiento in filas_asientos
    ]


def _listar_detalles_por_asiento_id(asiento_id: int) -> list[dict[str, Any]]:
    filas_detalles = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_ASIENTOS_CONTABLES_DETALLE}
        FROM asientos_contables_detalle
        WHERE asiento_id = ?
        ORDER BY renglon
        """,
        (asiento_id,),
    ).fetchall()

    return [
        _normalizar_fila_asiento_contable_detalle(fila_detalle)
        for fila_detalle in filas_detalles
    ]


def _validar_detalles_asiento(
    detalles_asiento: Any,
    asiento_default: dict[str, Any],
) -> list[dict[str, Any]]:
    try:
        detalles = list(detalles_asiento or [])
    except TypeError as exc:
        raise ValueError("El asiento debe tener detalle.") from exc

    if not detalles:
        raise ValueError("El asiento debe tener al menos un renglon.")

    detalles_validados: list[dict[str, Any]] = []

    for indice, detalle in enumerate(detalles, start=1):
        if not isinstance(detalle, dict):
            raise ValueError("Cada renglon del asiento debe ser un diccionario.")

        detalles_validados.append(
            _validar_detalle_asiento(detalle, indice, asiento_default)
        )

    return detalles_validados


def _validar_detalle_asiento(
    detalle: dict[str, Any],
    indice: int,
    asiento_default: dict[str, Any],
) -> dict[str, Any]:
    renglon = _validar_entero_positivo(
        detalle.get("renglon", indice),
        "El renglon debe ser un entero positivo.",
    )
    cuenta_contable_codigo = _validar_texto_obligatorio(
        detalle.get("cuenta_contable_codigo"),
        "La cuenta contable es obligatoria.",
    )
    descripcion = _normalizar_texto_opcional(detalle.get("descripcion"))
    moneda_codigo = _validar_codigo_moneda(
        detalle.get("moneda_codigo", asiento_default["moneda_origen_codigo"]),
        "La moneda del renglon es obligatoria.",
    )

    validar_moneda_activa(moneda_codigo)

    cotizacion_id_default = (
        asiento_default["cotizacion_id"]
        if moneda_codigo == asiento_default["moneda_origen_codigo"]
        else None
    )
    cotizacion_id = _validar_entero_positivo_opcional(
        detalle.get("cotizacion_id", cotizacion_id_default)
    )
    cotizacion_fecha = _validar_fecha_iso(
        detalle.get("cotizacion_fecha", asiento_default["cotizacion_fecha"]),
        "La fecha de cotizacion del renglon es obligatoria.",
    )
    cotizacion_tipo = _validar_opcion(
        detalle.get("cotizacion_tipo", asiento_default["cotizacion_tipo"]),
        _TIPOS_COTIZACION_VALIDOS,
        "El tipo de cotizacion del renglon es invalido.",
    )

    if "cotizacion_1000000" in detalle:
        cotizacion_1000000 = _validar_entero_positivo(
            detalle["cotizacion_1000000"],
            "La cotizacion del renglon debe ser un entero positivo.",
        )
    elif moneda_codigo == "ARS":
        cotizacion_1000000 = 1000000
    else:
        cotizacion_1000000 = int(asiento_default["cotizacion_1000000"])

    if moneda_codigo == "ARS":
        if cotizacion_1000000 != 1000000:
            raise ValueError("La cotizacion del renglon ARS debe ser 1000000.")
        if cotizacion_id is not None:
            raise ValueError("Un renglon ARS no debe referenciar cotizacion.")

    nominal_debe_centavos = _validar_centavos(
        detalle.get("nominal_debe_centavos", 0),
        "El nominal debe debe ser un entero no negativo.",
    )
    nominal_haber_centavos = _validar_centavos(
        detalle.get("nominal_haber_centavos", 0),
        "El nominal haber debe ser un entero no negativo.",
    )
    debe_centavos = _validar_centavos(
        detalle.get("debe_centavos", 0),
        "El debe contable debe ser un entero no negativo.",
    )
    haber_centavos = _validar_centavos(
        detalle.get("haber_centavos", 0),
        "El haber contable debe ser un entero no negativo.",
    )

    _validar_lado_importes(
        nominal_debe_centavos,
        nominal_haber_centavos,
        debe_centavos,
        haber_centavos,
    )

    return {
        "renglon": renglon,
        "cuenta_contable_codigo": cuenta_contable_codigo,
        "descripcion": descripcion,
        "moneda_codigo": moneda_codigo,
        "cotizacion_id": cotizacion_id,
        "cotizacion_fecha": cotizacion_fecha,
        "cotizacion_tipo": cotizacion_tipo,
        "cotizacion_1000000": cotizacion_1000000,
        "nominal_debe_centavos": nominal_debe_centavos,
        "nominal_haber_centavos": nominal_haber_centavos,
        "debe_centavos": debe_centavos,
        "haber_centavos": haber_centavos,
    }


def _validar_lado_importes(
    nominal_debe_centavos: int,
    nominal_haber_centavos: int,
    debe_centavos: int,
    haber_centavos: int,
) -> None:
    tiene_debe_contable = debe_centavos > 0 and haber_centavos == 0
    tiene_haber_contable = haber_centavos > 0 and debe_centavos == 0

    if not tiene_debe_contable and not tiene_haber_contable:
        raise ValueError("El renglon debe imputar debe o haber contable.")

    tiene_debe_nominal = nominal_debe_centavos > 0 and nominal_haber_centavos == 0
    tiene_haber_nominal = nominal_haber_centavos > 0 and nominal_debe_centavos == 0

    if not tiene_debe_nominal and not tiene_haber_nominal:
        raise ValueError("El renglon debe informar nominal debe o nominal haber.")

    if tiene_debe_contable and not tiene_debe_nominal:
        raise ValueError("El lado nominal debe coincidir con el lado contable.")

    if tiene_haber_contable and not tiene_haber_nominal:
        raise ValueError("El lado nominal debe coincidir con el lado contable.")


def _normalizar_fila_asiento_contable(fila_asiento) -> dict[str, Any]:
    asiento = dict(fila_asiento)

    for campo in ("id", "ejercicio_id", "cotizacion_1000000"):
        asiento[campo] = int(asiento[campo])

    for campo in ("numero_asiento", "cotizacion_id", "asiento_reversion_id"):
        if asiento[campo] is not None:
            asiento[campo] = int(asiento[campo])

    return asiento


def _normalizar_fila_asiento_contable_detalle(fila_detalle) -> dict[str, Any]:
    detalle = dict(fila_detalle)

    for campo in (
        "id",
        "asiento_id",
        "renglon",
        "cotizacion_1000000",
        "nominal_debe_centavos",
        "nominal_haber_centavos",
        "debe_centavos",
        "haber_centavos",
    ):
        detalle[campo] = int(detalle[campo])

    if detalle["cotizacion_id"] is not None:
        detalle["cotizacion_id"] = int(detalle["cotizacion_id"])

    return detalle


def _validar_codigo_moneda(codigo_moneda: Any, mensaje_obligatorio: str) -> str:
    codigo_moneda_validado = str(codigo_moneda or "").strip().upper()

    if not codigo_moneda_validado:
        raise ValueError(mensaje_obligatorio)

    if len(codigo_moneda_validado) != 3 or not codigo_moneda_validado.isalpha():
        raise ValueError("El codigo de moneda debe tener formato AAA.")

    return codigo_moneda_validado


def _validar_fecha_iso(fecha: Any, mensaje_obligatorio: str) -> str:
    fecha_validada = str(fecha or "").strip()

    if not fecha_validada:
        raise ValueError(mensaje_obligatorio)

    if not _PATRON_FECHA_ISO.match(fecha_validada):
        raise ValueError("La fecha debe tener formato YYYY-MM-DD.")

    try:
        datetime.strptime(fecha_validada, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("La fecha debe ser una fecha valida.") from exc

    return fecha_validada


def _validar_opcion(valor: Any, opciones_validas: set[str], mensaje_error: str) -> str:
    valor_validado = str(valor or "").strip().upper()

    if valor_validado not in opciones_validas:
        raise ValueError(mensaje_error)

    return valor_validado


def _validar_texto_obligatorio(valor: Any, mensaje_error: str) -> str:
    valor_validado = str(valor or "").strip()

    if not valor_validado:
        raise ValueError(mensaje_error)

    return valor_validado


def _normalizar_texto_opcional(valor: Any) -> str | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return valor_normalizado


def _validar_entero_positivo(valor: Any, mensaje_error: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje_error)

    try:
        valor_validado = int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(mensaje_error) from exc

    if valor_validado <= 0:
        raise ValueError(mensaje_error)

    return valor_validado


def _validar_entero_positivo_opcional(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None

    return _validar_entero_positivo(valor, "El valor debe ser un entero positivo.")


def _validar_centavos(valor: Any, mensaje_error: str) -> int:
    if isinstance(valor, bool):
        raise ValueError(mensaje_error)

    try:
        valor_validado = int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(mensaje_error) from exc

    if valor_validado < 0:
        raise ValueError(mensaje_error)

    return valor_validado


def _validar_limite(limite: Any) -> int:
    if isinstance(limite, bool):
        raise ValueError("El limite es invalido.")

    try:
        limite_validado = int(limite)
    except (TypeError, ValueError) as exc:
        raise ValueError("El limite es invalido.") from exc

    if limite_validado < 1 or limite_validado > 500:
        raise ValueError("El limite debe estar entre 1 y 500.")

    return limite_validado
