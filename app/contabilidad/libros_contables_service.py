from typing import Any

from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_activo,
    obtener_ejercicio_contable_por_id,
)
from app.contabilidad.libros_contables_repository import (
    listar_movimientos_libro_diario,
)
from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
)

_PREFIJO_COMPROBANTE = "Comprobante:"
_PREFIJO_SUJETO = "Sujeto:"


def obtener_contexto_libro_diario(
    ejercicio_id: Any,
    fecha_desde: Any = None,
    fecha_hasta: Any = None,
    estado: Any = "CONFIRMADO",
) -> dict[str, Any]:
    """
    Devuelve el Libro Diario agrupado por asiento.

    El service no ejecuta SQL. Toma movimientos planos del repository y prepara
    datos de lectura: comprobante, sujeto, renglones, totales por asiento y
    totales generales.
    """
    movimientos = listar_movimientos_libro_diario(
        ejercicio_id,
        fecha_desde,
        fecha_hasta,
        estado,
    )
    asientos = _agrupar_movimientos_por_asiento(movimientos)
    total_debe_centavos = sum(asiento["total_debe_centavos"] for asiento in asientos)
    total_haber_centavos = sum(asiento["total_haber_centavos"] for asiento in asientos)
    diferencia_centavos = total_debe_centavos - total_haber_centavos

    return {
        "filtros": {
            "ejercicio_id": ejercicio_id,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "estado": estado,
        },
        "libro_diario_asientos": asientos,
        "cantidad_asientos": len(asientos),
        "total_debe_centavos": total_debe_centavos,
        "total_haber_centavos": total_haber_centavos,
        "diferencia_centavos": diferencia_centavos,
        "total_debe_argentina": _formatear_centavos(total_debe_centavos),
        "total_haber_argentina": _formatear_centavos(total_haber_centavos),
        "diferencia_argentina": _formatear_centavos(diferencia_centavos),
    }


def _agrupar_movimientos_por_asiento(
    movimientos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    asientos_por_id: dict[int, dict[str, Any]] = {}
    asientos: list[dict[str, Any]] = []

    for movimiento in movimientos:
        asiento_id = int(movimiento["asiento_id"])

        if asiento_id not in asientos_por_id:
            comprobante, sujeto = _extraer_comprobante_y_sujeto(
                movimiento.get("asiento_descripcion")
            )
            asiento = {
                "asiento_id": asiento_id,
                "ejercicio_id": int(movimiento["ejercicio_id"]),
                "ejercicio_codigo": movimiento.get("ejercicio_codigo"),
                "numero_asiento": movimiento.get("numero_asiento"),
                "numero_asiento_mostrar": _formatear_numero_asiento(
                    movimiento.get("ejercicio_codigo"),
                    movimiento.get("numero_asiento"),
                ),
                "fecha": movimiento.get("fecha"),
                "fecha_argentina": _formatear_fecha(movimiento.get("fecha")),
                "estado": movimiento.get("estado"),
                "tipo": movimiento.get("tipo"),
                "descripcion": movimiento.get("asiento_descripcion") or "",
                "comprobante": comprobante,
                "sujeto": sujeto,
                "renglones": [],
                "total_debe_centavos": 0,
                "total_haber_centavos": 0,
                "diferencia_centavos": 0,
                "total_debe_argentina": "0,00",
                "total_haber_argentina": "0,00",
                "diferencia_argentina": "0,00",
            }
            asientos_por_id[asiento_id] = asiento
            asientos.append(asiento)

        asiento = asientos_por_id[asiento_id]
        debe_centavos = int(movimiento["debe_centavos"])
        haber_centavos = int(movimiento["haber_centavos"])

        asiento["renglones"].append(
            {
                "detalle_id": int(movimiento["detalle_id"]),
                "renglon": int(movimiento["renglon"]),
                "cuenta": movimiento.get("cuenta_contable_codigo"),
                "cuenta_nombre": movimiento.get("cuenta_nombre"),
                "descripcion": movimiento.get("detalle_descripcion") or "",
                "debe_centavos": debe_centavos,
                "haber_centavos": haber_centavos,
                "debe_argentina": _formatear_centavos(debe_centavos),
                "haber_argentina": _formatear_centavos(haber_centavos),
            }
        )
        asiento["total_debe_centavos"] += debe_centavos
        asiento["total_haber_centavos"] += haber_centavos
        asiento["diferencia_centavos"] = (
            asiento["total_debe_centavos"] - asiento["total_haber_centavos"]
        )
        asiento["total_debe_argentina"] = _formatear_centavos(
            asiento["total_debe_centavos"]
        )
        asiento["total_haber_argentina"] = _formatear_centavos(
            asiento["total_haber_centavos"]
        )
        asiento["diferencia_argentina"] = _formatear_centavos(
            asiento["diferencia_centavos"]
        )

    return asientos


def _extraer_comprobante_y_sujeto(descripcion: Any) -> tuple[str, str]:
    texto = str(descripcion or "").strip()
    comprobante = ""
    sujeto = ""

    for parte in texto.split("|"):
        parte_normalizada = parte.strip()

        if parte_normalizada.startswith(_PREFIJO_COMPROBANTE):
            comprobante = parte_normalizada[len(_PREFIJO_COMPROBANTE) :].strip()
            continue

        if parte_normalizada.startswith(_PREFIJO_SUJETO):
            sujeto = parte_normalizada[len(_PREFIJO_SUJETO) :].strip()

    return comprobante, sujeto


def _formatear_numero_asiento(ejercicio_codigo: Any, numero_asiento: Any) -> str:
    if numero_asiento is None:
        return "Borrador"

    codigo = str(ejercicio_codigo or "").strip().upper()
    prefijo = codigo if codigo.startswith("EJ") else f"EJ{codigo}"
    return f"{prefijo}-{int(numero_asiento):07d}"


def _formatear_fecha(fecha: Any) -> str:
    fecha_normalizada = str(fecha or "").strip()

    if not fecha_normalizada:
        return ""

    return formatear_fecha_iso_a_argentina(fecha_normalizada)


def _formatear_centavos(valor: Any) -> str:
    return formatear_entero_escala_a_decimal_argentino(int(valor or 0), 2)


_ESTADOS_PANTALLA_LIBRO_DIARIO = [
    {"codigo": "CONFIRMADO", "descripcion": "Confirmados"},
    {"codigo": "BORRADOR", "descripcion": "Borradores"},
    {"codigo": "ANULADO", "descripcion": "Anulados"},
]


def obtener_contexto_pantalla_libro_diario(filtros: Any | None = None) -> dict[str, Any]:
    """
    Devuelve contexto de pantalla para Libro Diario.

    Resuelve ejercicio activo y filtros visibles. La lectura contable queda
    delegada a obtener_contexto_libro_diario.
    """
    filtros_dict = dict(filtros or {})
    ejercicio_id_filtro = _normalizar_entero_positivo_opcional(
        filtros_dict.get("ejercicio_id")
    )

    if ejercicio_id_filtro is None:
        ejercicio = obtener_ejercicio_contable_activo()
    else:
        ejercicio = obtener_ejercicio_contable_por_id(ejercicio_id_filtro)
        if ejercicio is None:
            raise ValueError("No existe el ejercicio contable seleccionado.")

    fecha_desde = (
        _normalizar_texto_opcional(filtros_dict.get("fecha_desde"))
        or ejercicio["fecha_desde"]
    )
    fecha_hasta = (
        _normalizar_texto_opcional(filtros_dict.get("fecha_hasta"))
        or ejercicio["fecha_hasta"]
    )
    estado = _normalizar_estado_pantalla(filtros_dict.get("estado"))

    contexto = obtener_contexto_libro_diario(
        ejercicio["id"],
        fecha_desde,
        fecha_hasta,
        estado,
    )
    contexto["ejercicio_contable"] = _preparar_ejercicio_para_pantalla_libro_diario(
        ejercicio
    )
    contexto["estados_libro_diario"] = list(_ESTADOS_PANTALLA_LIBRO_DIARIO)
    contexto["filtros"] = {
        "ejercicio_id": str(ejercicio["id"]),
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "estado": estado,
    }

    return contexto


def _preparar_ejercicio_para_pantalla_libro_diario(
    ejercicio: dict[str, Any],
) -> dict[str, Any]:
    ejercicio_pantalla = dict(ejercicio)
    ejercicio_pantalla["fecha_desde_argentina"] = formatear_fecha_iso_a_argentina(
        ejercicio["fecha_desde"]
    )
    ejercicio_pantalla["fecha_hasta_argentina"] = formatear_fecha_iso_a_argentina(
        ejercicio["fecha_hasta"]
    )
    return ejercicio_pantalla


def _normalizar_estado_pantalla(valor: Any) -> str:
    estado = str(valor or "CONFIRMADO").strip().upper()

    if not estado:
        return "CONFIRMADO"

    estados_validos = {
        estado_libro["codigo"] for estado_libro in _ESTADOS_PANTALLA_LIBRO_DIARIO
    }
    if estado not in estados_validos:
        raise ValueError("El estado del asiento es invalido.")

    return estado


def _normalizar_entero_positivo_opcional(valor: Any) -> int | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    try:
        valor_entero = int(valor_normalizado)
    except ValueError as exc:
        raise ValueError("El id del ejercicio contable es obligatorio.") from exc

    if valor_entero <= 0:
        raise ValueError("El id del ejercicio contable es obligatorio.")

    return valor_entero


def _normalizar_texto_opcional(valor: Any) -> str | None:
    valor_normalizado = str(valor or "").strip()
    return valor_normalizado or None
