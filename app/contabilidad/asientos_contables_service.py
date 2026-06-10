from typing import Any

from app.contabilidad.asientos_contables_repository import (
    crear_asiento_contable,
    listar_asientos_contables_por_ejercicio,
    obtener_asiento_contable_por_id,
)
from app.contabilidad.cuentas_contables_repository import (
    validar_cuenta_contable_imputable,
)
from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_activo,
    obtener_ejercicio_contable_por_fecha,
)
from app.shared.monedas_cotizaciones_repository import (
    obtener_ultima_moneda_cotizacion,
)
from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
)

_MONEDA_CONTABLE = "ARS"
_TIPO_COTIZACION_DEFAULT = "CIERRE"


def crear_asiento_contable_borrador(
    datos_asiento: dict[str, Any],
    detalles_asiento: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Crea un asiento contable en borrador.

    El service aplica reglas de negocio: ejercicio vigente, cuentas imputables,
    contabilidad siempre en ARS y balance entre debe/haber contable.
    """
    datos_validados = _copiar_dict(datos_asiento, "Los datos del asiento son obligatorios.")

    fecha = str(datos_validados.get("fecha") or "").strip()
    ejercicio_id = _validar_entero_positivo(
        datos_validados.get("ejercicio_id"),
        "El ejercicio contable es obligatorio.",
    )

    _validar_ejercicio_operacion(ejercicio_id, fecha)

    datos_validados["ejercicio_id"] = ejercicio_id
    datos_validados["estado"] = "BORRADOR"
    datos_validados.setdefault("tipo", "MANUAL")
    datos_validados.setdefault("moneda_origen_codigo", _MONEDA_CONTABLE)
    datos_validados["moneda_destino_codigo"] = _MONEDA_CONTABLE
    datos_validados.setdefault("cotizacion_tipo", _TIPO_COTIZACION_DEFAULT)
    datos_validados = _resolver_cotizacion_cabecera(datos_validados, fecha)

    detalles_validados = _validar_y_completar_detalles(
        detalles_asiento,
        datos_validados,
        fecha,
    )
    _validar_balance_ars(detalles_validados)

    return crear_asiento_contable(datos_validados, detalles_validados)


def obtener_asiento_contable(asiento_id: Any) -> dict[str, Any] | None:
    """Devuelve un asiento contable con detalle."""
    return obtener_asiento_contable_por_id(asiento_id)


def listar_asientos_contables(
    ejercicio_id: Any,
    limite: int = 100,
) -> list[dict[str, Any]]:
    """Devuelve cabeceras de asientos contables para un ejercicio."""
    return listar_asientos_contables_por_ejercicio(ejercicio_id, limite)


def obtener_contexto_listado_asientos_contables(
    limite: int = 100,
) -> dict[str, Any]:
    """
    Devuelve contexto de pantalla para listado inicial de asientos.

    La pantalla lista cabeceras y totales calculados desde el detalle, sin
    resolver carga ni confirmacion de asientos.
    """
    try:
        ejercicio_contable_activo = obtener_ejercicio_contable_activo()
    except ValueError:
        return {
            "ejercicio_contable_activo": None,
            "asientos_contables": [],
            "cantidad_asientos_contables": 0,
            "mensaje_contexto_asientos": "Sin ejercicio contable activo.",
        }

    asientos = listar_asientos_contables_por_ejercicio(
        ejercicio_contable_activo["id"],
        limite,
    )
    asientos_pantalla = [
        _preparar_asiento_contable_para_listado(asiento)
        for asiento in asientos
    ]

    return {
        "ejercicio_contable_activo": _preparar_ejercicio_contable_activo_para_listado(
            ejercicio_contable_activo
        ),
        "asientos_contables": asientos_pantalla,
        "cantidad_asientos_contables": len(asientos_pantalla),
        "mensaje_contexto_asientos": "",
    }


def _preparar_ejercicio_contable_activo_para_listado(
    ejercicio_contable: dict[str, Any],
) -> dict[str, Any]:
    ejercicio_contable_pantalla = dict(ejercicio_contable)
    ejercicio_contable_pantalla["fecha_desde_argentina"] = (
        formatear_fecha_iso_a_argentina(ejercicio_contable["fecha_desde"])
    )
    ejercicio_contable_pantalla["fecha_hasta_argentina"] = (
        formatear_fecha_iso_a_argentina(ejercicio_contable["fecha_hasta"])
    )

    return ejercicio_contable_pantalla


def _preparar_asiento_contable_para_listado(
    asiento: dict[str, Any],
) -> dict[str, Any]:
    asiento_pantalla = dict(asiento)
    asiento_con_detalle = obtener_asiento_contable_por_id(asiento["id"])
    detalles = asiento_con_detalle["detalles"] if asiento_con_detalle else []

    total_debe_centavos = sum(
        int(detalle["debe_centavos"])
        for detalle in detalles
    )
    total_haber_centavos = sum(
        int(detalle["haber_centavos"])
        for detalle in detalles
    )

    asiento_pantalla["fecha_argentina"] = formatear_fecha_iso_a_argentina(
        asiento["fecha"]
    )
    asiento_pantalla["numero_asiento_mostrar"] = (
        str(asiento["numero_asiento"])
        if asiento["numero_asiento"] is not None
        else "Borrador"
    )
    asiento_pantalla["estado_codigo"] = asiento["estado"]
    asiento_pantalla["tipo_codigo"] = asiento["tipo"]
    asiento_pantalla["moneda_operacion_codigo"] = asiento["moneda_origen_codigo"]
    asiento_pantalla["par_monedas_codigo"] = (
        f"{asiento['moneda_origen_codigo']}/{asiento['moneda_destino_codigo']}"
    )
    asiento_pantalla["cotizacion_mostrar"] = _formatear_cotizacion_asiento(asiento)
    asiento_pantalla["total_debe_argentina"] = (
        formatear_entero_escala_a_decimal_argentino(total_debe_centavos, 2)
    )
    asiento_pantalla["total_haber_argentina"] = (
        formatear_entero_escala_a_decimal_argentino(total_haber_centavos, 2)
    )

    return asiento_pantalla


def _formatear_cotizacion_asiento(asiento: dict[str, Any]) -> str:
    if asiento["moneda_origen_codigo"] == _MONEDA_CONTABLE:
        return "1,000000"

    return formatear_entero_escala_a_decimal_argentino(
        int(asiento["cotizacion_1000000"]),
        6,
    )


def obtener_contexto_detalle_asiento_contable(
    asiento_id: Any,
) -> dict[str, Any]:
    """
    Devuelve contexto de pantalla para detalle de asiento contable.

    La pantalla es de solo lectura. No confirma, anula ni modifica el asiento.
    """
    asiento = obtener_asiento_contable_por_id(asiento_id)

    if asiento is None:
        raise ValueError("No existe el asiento contable informado.")

    asiento_pantalla = _preparar_asiento_contable_para_listado(asiento)
    detalles_pantalla = [
        _preparar_detalle_asiento_contable_para_pantalla(detalle)
        for detalle in asiento["detalles"]
    ]

    return {
        "asiento_contable": asiento_pantalla,
        "detalles_asiento_contable": detalles_pantalla,
        "cantidad_renglones_asiento": len(detalles_pantalla),
    }


def _preparar_detalle_asiento_contable_para_pantalla(
    detalle: dict[str, Any],
) -> dict[str, Any]:
    detalle_pantalla = dict(detalle)
    detalle_pantalla["descripcion_mostrar"] = detalle["descripcion"] or ""
    detalle_pantalla["cotizacion_mostrar"] = _formatear_cotizacion_detalle(detalle)
    detalle_pantalla["nominal_debe_argentina"] = _formatear_importe_cero_vacio(
        detalle["nominal_debe_centavos"]
    )
    detalle_pantalla["nominal_haber_argentina"] = _formatear_importe_cero_vacio(
        detalle["nominal_haber_centavos"]
    )
    detalle_pantalla["debe_argentina"] = _formatear_importe_cero_vacio(
        detalle["debe_centavos"]
    )
    detalle_pantalla["haber_argentina"] = _formatear_importe_cero_vacio(
        detalle["haber_centavos"]
    )

    return detalle_pantalla


def _formatear_cotizacion_detalle(detalle: dict[str, Any]) -> str:
    if detalle["moneda_codigo"] == _MONEDA_CONTABLE:
        return "1,000000"

    return formatear_entero_escala_a_decimal_argentino(
        int(detalle["cotizacion_1000000"]),
        6,
    )


def _formatear_importe_cero_vacio(importe_centavos: Any) -> str:
    importe_validado = int(importe_centavos)

    if importe_validado == 0:
        return ""

    return formatear_entero_escala_a_decimal_argentino(importe_validado, 2)


def _validar_ejercicio_operacion(ejercicio_id: int, fecha: str) -> None:
    ejercicio = obtener_ejercicio_contable_por_fecha(fecha)

    if ejercicio is None:
        raise ValueError("No existe ejercicio contable para la fecha informada.")

    if int(ejercicio["id"]) != ejercicio_id:
        raise ValueError("La fecha no corresponde al ejercicio contable informado.")

    if ejercicio["estado"] != "ABIERTO":
        raise ValueError("El ejercicio contable no esta abierto.")

    if int(ejercicio["bloqueado"]) == 1:
        raise ValueError("El ejercicio contable esta bloqueado.")


def _resolver_cotizacion_cabecera(
    datos_asiento: dict[str, Any],
    fecha: str,
) -> dict[str, Any]:
    moneda_origen_codigo = _validar_codigo_moneda(
        datos_asiento.get("moneda_origen_codigo", _MONEDA_CONTABLE),
        "La moneda origen es obligatoria.",
    )
    moneda_destino_codigo = _validar_codigo_moneda(
        datos_asiento.get("moneda_destino_codigo", _MONEDA_CONTABLE),
        "La moneda destino es obligatoria.",
    )

    if moneda_destino_codigo != _MONEDA_CONTABLE:
        raise ValueError("La moneda contable destino debe ser ARS.")

    datos_asiento["moneda_origen_codigo"] = moneda_origen_codigo
    datos_asiento["moneda_destino_codigo"] = moneda_destino_codigo

    if moneda_origen_codigo == _MONEDA_CONTABLE:
        datos_asiento["cotizacion_id"] = None
        datos_asiento["cotizacion_fecha"] = fecha
        datos_asiento["cotizacion_tipo"] = _TIPO_COTIZACION_DEFAULT
        datos_asiento["cotizacion_1000000"] = 1000000
        return datos_asiento

    cotizacion_tipo = str(
        datos_asiento.get("cotizacion_tipo") or _TIPO_COTIZACION_DEFAULT
    ).strip().upper()

    if _tiene_cotizacion_completa(datos_asiento):
        datos_asiento["cotizacion_tipo"] = cotizacion_tipo
        return datos_asiento

    cotizacion = obtener_ultima_moneda_cotizacion(
        moneda_origen_codigo,
        _MONEDA_CONTABLE,
        cotizacion_tipo,
        fecha,
    )

    if cotizacion is None:
        raise ValueError("No existe cotizacion disponible para la moneda del asiento.")

    datos_asiento["cotizacion_id"] = cotizacion["id"]
    datos_asiento["cotizacion_fecha"] = cotizacion["fecha"]
    datos_asiento["cotizacion_tipo"] = cotizacion["tipo"]
    datos_asiento["cotizacion_1000000"] = cotizacion["cotizacion_1000000"]

    return datos_asiento


def _validar_y_completar_detalles(
    detalles_asiento: Any,
    datos_asiento: dict[str, Any],
    fecha: str,
) -> list[dict[str, Any]]:
    try:
        detalles = list(detalles_asiento or [])
    except TypeError as exc:
        raise ValueError("El asiento debe tener detalle.") from exc

    if not detalles:
        raise ValueError("El asiento debe tener al menos un renglon.")

    detalles_validados: list[dict[str, Any]] = []

    for indice, detalle in enumerate(detalles, start=1):
        detalle_validado = _copiar_dict(
            detalle,
            "Cada renglon del asiento debe ser un diccionario.",
        )
        detalle_validado.setdefault("renglon", indice)

        cuenta_contable_codigo = str(
            detalle_validado.get("cuenta_contable_codigo") or ""
        ).strip()
        validar_cuenta_contable_imputable(cuenta_contable_codigo)
        detalle_validado["cuenta_contable_codigo"] = cuenta_contable_codigo

        detalle_validado = _resolver_cotizacion_detalle(
            detalle_validado,
            datos_asiento,
            fecha,
        )

        detalles_validados.append(detalle_validado)

    return detalles_validados


def _resolver_cotizacion_detalle(
    detalle: dict[str, Any],
    datos_asiento: dict[str, Any],
    fecha: str,
) -> dict[str, Any]:
    moneda_codigo = _validar_codigo_moneda(
        detalle.get("moneda_codigo", datos_asiento["moneda_origen_codigo"]),
        "La moneda del renglon es obligatoria.",
    )
    detalle["moneda_codigo"] = moneda_codigo

    if moneda_codigo == _MONEDA_CONTABLE:
        detalle["cotizacion_id"] = None
        detalle["cotizacion_fecha"] = fecha
        detalle["cotizacion_tipo"] = _TIPO_COTIZACION_DEFAULT
        detalle["cotizacion_1000000"] = 1000000
        return detalle

    cotizacion_tipo = str(
        detalle.get("cotizacion_tipo")
        or datos_asiento.get("cotizacion_tipo")
        or _TIPO_COTIZACION_DEFAULT
    ).strip().upper()

    if _tiene_cotizacion_completa(detalle):
        detalle["cotizacion_tipo"] = cotizacion_tipo
        return detalle

    if moneda_codigo == datos_asiento["moneda_origen_codigo"] and _tiene_cotizacion_completa(
        datos_asiento
    ):
        detalle["cotizacion_id"] = datos_asiento["cotizacion_id"]
        detalle["cotizacion_fecha"] = datos_asiento["cotizacion_fecha"]
        detalle["cotizacion_tipo"] = datos_asiento["cotizacion_tipo"]
        detalle["cotizacion_1000000"] = datos_asiento["cotizacion_1000000"]
        return detalle

    cotizacion = obtener_ultima_moneda_cotizacion(
        moneda_codigo,
        _MONEDA_CONTABLE,
        cotizacion_tipo,
        fecha,
    )

    if cotizacion is None:
        raise ValueError("No existe cotizacion disponible para la moneda del renglon.")

    detalle["cotizacion_id"] = cotizacion["id"]
    detalle["cotizacion_fecha"] = cotizacion["fecha"]
    detalle["cotizacion_tipo"] = cotizacion["tipo"]
    detalle["cotizacion_1000000"] = cotizacion["cotizacion_1000000"]

    return detalle


def _validar_balance_ars(detalles: list[dict[str, Any]]) -> None:
    total_debe_centavos = sum(
        _validar_centavos(detalle.get("debe_centavos", 0), "El debe es invalido.")
        for detalle in detalles
    )
    total_haber_centavos = sum(
        _validar_centavos(detalle.get("haber_centavos", 0), "El haber es invalido.")
        for detalle in detalles
    )

    if total_debe_centavos <= 0 and total_haber_centavos <= 0:
        raise ValueError("El asiento debe tener importe.")

    if total_debe_centavos != total_haber_centavos:
        raise ValueError("El asiento contable no balancea.")


def _tiene_cotizacion_completa(datos: dict[str, Any]) -> bool:
    return (
        datos.get("cotizacion_id") not in (None, "")
        and datos.get("cotizacion_fecha") not in (None, "")
        and datos.get("cotizacion_tipo") not in (None, "")
        and datos.get("cotizacion_1000000") not in (None, "")
    )


def _copiar_dict(valor: Any, mensaje_error: str) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise ValueError(mensaje_error)

    return dict(valor)


def _validar_codigo_moneda(codigo_moneda: Any, mensaje_obligatorio: str) -> str:
    codigo_moneda_validado = str(codigo_moneda or "").strip().upper()

    if not codigo_moneda_validado:
        raise ValueError(mensaje_obligatorio)

    if len(codigo_moneda_validado) != 3 or not codigo_moneda_validado.isalpha():
        raise ValueError("El codigo de moneda debe tener formato AAA.")

    return codigo_moneda_validado


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
