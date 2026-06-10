from typing import Any

from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_hora_sql_a_argentina,
    formatear_fecha_iso_a_argentina,
    normalizar_decimal_argentino_a_entero_escala,
    normalizar_fecha_argentina_a_iso,
)
from app.shared.monedas_cotizaciones_repository import (
    crear_moneda_cotizacion,
    listar_monedas_cotizaciones_por_par,
    listar_monedas_cotizaciones_recientes,
    obtener_ultima_moneda_cotizacion,
)


def obtener_contexto_cotizaciones_recientes(limite: int = 100) -> dict[str, Any]:
    """
    Devuelve contexto chico de cotizaciones recientes.

    Este service no ejecuta SQL directo. La lectura queda delegada al
    repository transversal de monedas_cotizaciones.
    """
    cotizaciones = [
        _preparar_cotizacion_para_pantalla(cotizacion)
        for cotizacion in listar_monedas_cotizaciones_recientes(limite)
    ]

    return {
        "cotizaciones": cotizaciones,
        "cantidad_cotizaciones": len(cotizaciones),
    }


def obtener_contexto_cotizaciones_por_par(
    moneda_origen_codigo: Any,
    moneda_destino_codigo: Any,
    tipo: Any = "CIERRE",
    limite: int = 100,
) -> dict[str, Any]:
    """Devuelve contexto chico de cotizaciones de un par."""
    cotizaciones = [
        _preparar_cotizacion_para_pantalla(cotizacion)
        for cotizacion in listar_monedas_cotizaciones_por_par(
            moneda_origen_codigo,
            moneda_destino_codigo,
            tipo,
            limite,
        )
    ]

    return {
        "cotizaciones": cotizaciones,
        "cantidad_cotizaciones": len(cotizaciones),
    }


def obtener_ultima_cotizacion_para_operacion(
    moneda_origen_codigo: Any,
    moneda_destino_codigo: Any,
    tipo: Any = "CIERRE",
    fecha_hasta: Any | None = None,
) -> dict[str, Any]:
    """Devuelve la ultima cotizacion disponible preparada para uso operativo."""
    fecha_hasta_iso = (
        _normalizar_fecha_formulario(fecha_hasta)
        if fecha_hasta is not None
        else None
    )

    cotizacion = obtener_ultima_moneda_cotizacion(
        moneda_origen_codigo,
        moneda_destino_codigo,
        tipo,
        fecha_hasta_iso,
    )

    if cotizacion is None:
        raise ValueError("No existe cotizacion para el par de monedas informado.")

    return _preparar_cotizacion_para_pantalla(cotizacion)


def crear_moneda_cotizacion_desde_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """
    Crea una cotizacion desde datos de formulario.

    El service no ejecuta SQL directo. Normaliza entrada de pantalla y delega la
    persistencia al repository de monedas_cotizaciones.
    """
    datos_cotizacion = _normalizar_datos_cotizacion_formulario(formulario)

    cotizacion = crear_moneda_cotizacion(datos_cotizacion)

    return _preparar_cotizacion_para_pantalla(cotizacion)


def _normalizar_datos_cotizacion_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza campos de formulario de monedas_cotizaciones."""
    return {
        "moneda_origen_codigo": _obtener_valor_formulario(
            formulario,
            "moneda_origen_codigo",
        ).upper(),
        "moneda_destino_codigo": _obtener_valor_formulario(
            formulario,
            "moneda_destino_codigo",
        ).upper(),
        "fecha": _normalizar_fecha_formulario(
            _obtener_valor_formulario(formulario, "fecha")
        ),
        "tipo": _obtener_valor_formulario(formulario, "tipo").upper() or "CIERRE",
        "cotizacion_1000000": normalizar_decimal_argentino_a_entero_escala(
            _obtener_valor_formulario(formulario, "cotizacion"),
            6,
        ),
        "fuente": _obtener_valor_formulario(formulario, "fuente"),
        "observaciones": _obtener_valor_formulario(formulario, "observaciones"),
    }


def _preparar_cotizacion_para_pantalla(
    cotizacion: dict[str, Any],
) -> dict[str, Any]:
    """Agrega campos de presentacion sin modificar el contrato de repository."""
    cotizacion_pantalla = dict(cotizacion)

    cotizacion_pantalla["fecha_argentina"] = formatear_fecha_iso_a_argentina(
        cotizacion["fecha"]
    )
    cotizacion_pantalla["cotizacion_argentina"] = (
        formatear_entero_escala_a_decimal_argentino(
            cotizacion["cotizacion_1000000"],
            6,
        )
    )
    cotizacion_pantalla["creado_en_argentina"] = (
        formatear_fecha_hora_sql_a_argentina(cotizacion["creado_en"])
    )
    cotizacion_pantalla["actualizado_en_argentina"] = (
        formatear_fecha_hora_sql_a_argentina(cotizacion["actualizado_en"])
        if cotizacion.get("actualizado_en")
        else None
    )

    return cotizacion_pantalla


def _normalizar_fecha_formulario(fecha: Any) -> str:
    """Normaliza fecha recibida como DD/MM/YYYY o YYYY-MM-DD."""
    fecha_normalizada = str(fecha or "").strip()

    if not fecha_normalizada:
        raise ValueError("La fecha de cotizacion es obligatoria.")

    if "/" in fecha_normalizada:
        return normalizar_fecha_argentina_a_iso(fecha_normalizada)

    formatear_fecha_iso_a_argentina(fecha_normalizada)

    return fecha_normalizada


def _obtener_valor_formulario(formulario: dict[str, Any], campo: str) -> str:
    """Lee valor de formulario y devuelve texto recortado."""
    return str(formulario.get(campo, "") or "").strip()
