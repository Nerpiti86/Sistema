from datetime import date
from typing import Any

from app.contabilidad.coeficientes_inflacion_repository import (
    listar_coeficientes_inflacion_por_ejercicio_id,
    obtener_indice_inflacion,
    obtener_ultimo_indice_inflacion,
    reemplazar_coeficientes_inflacion_ejercicio,
)
from app.contabilidad.ejercicios_contables_repository import (
    obtener_ejercicio_contable_por_codigo,
)
from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_hora_sql_a_argentina,
    formatear_periodo_yyyymm_a_argentina,
)

_ESCALA_COEFICIENTE_INFLACION = 1_000_000_000_000


def generar_coeficientes_inflacion_ejercicio(
    ejercicio_contable_codigo: str,
) -> list[dict[str, Any]]:
    """
    Genera y persiste los 12 coeficientes de inflacion de un ejercicio.

    El service no ejecuta SQL directo. Lee indices y ejercicio por repository,
    calcula con enteros escalados y delega el snapshot al repository.
    """
    ejercicio_contable = _obtener_ejercicio_contable_existente(
        ejercicio_contable_codigo
    )
    indice_cierre = obtener_ultimo_indice_inflacion()

    if indice_cierre is None:
        raise ValueError("No existen indices de inflacion cargados.")

    periodos_ejercicio = derivar_doce_periodos_ejercicio(
        ejercicio_contable["fecha_desde"]
    )

    coeficientes_pendientes = []
    periodos_sin_indice = []

    for periodo_yyyymm in periodos_ejercicio:
        indice_inicio = obtener_indice_inflacion(periodo_yyyymm)

        if indice_inicio is None:
            periodos_sin_indice.append(
                formatear_periodo_yyyymm_a_argentina(periodo_yyyymm)
            )
            continue

        coeficientes_pendientes.append(
            {
                "periodo_yyyymm": periodo_yyyymm,
                "indice_inicio_10000": indice_inicio["indice_10000"],
                "indice_cierre_periodo_yyyymm": indice_cierre["periodo_yyyymm"],
                "indice_cierre_10000": indice_cierre["indice_10000"],
                "coeficiente_1000000000000": calcular_coeficiente_inflacion(
                    indice_inicio["indice_10000"],
                    indice_cierre["indice_10000"],
                ),
            }
        )

    if periodos_sin_indice:
        periodos = ", ".join(periodos_sin_indice)
        raise ValueError(f"Faltan indices de inflacion para: {periodos}.")

    coeficientes_guardados = reemplazar_coeficientes_inflacion_ejercicio(
        ejercicio_contable["id"],
        coeficientes_pendientes,
    )

    return [
        preparar_coeficiente_inflacion_para_pantalla(coeficiente)
        for coeficiente in coeficientes_guardados
    ]


def obtener_contexto_coeficientes_inflacion_ejercicio(
    ejercicio_contable_codigo: str,
) -> dict[str, Any]:
    """
    Devuelve contexto de coeficientes de inflacion para pantalla.

    No calcula ni persiste. Solo toma el snapshot existente y agrega campos
    argentinos visibles para que el template no transforme valores.
    """
    ejercicio_contable = _obtener_ejercicio_contable_existente(
        ejercicio_contable_codigo
    )
    coeficientes_inflacion = [
        preparar_coeficiente_inflacion_para_pantalla(coeficiente)
        for coeficiente in listar_coeficientes_inflacion_por_ejercicio_id(
            ejercicio_contable["id"]
        )
    ]

    return {
        "coeficientes_inflacion": coeficientes_inflacion,
        "cantidad_coeficientes_inflacion": len(coeficientes_inflacion),
        "tiene_coeficientes_inflacion": bool(coeficientes_inflacion),
    }


def derivar_doce_periodos_ejercicio(fecha_desde_iso: str) -> list[int]:
    """Deriva 12 periodos mensuales desde la fecha inicial del ejercicio."""
    if not isinstance(fecha_desde_iso, str):
        raise ValueError("La fecha desde del ejercicio debe ser texto ISO.")

    try:
        fecha_desde = date.fromisoformat(fecha_desde_iso)
    except ValueError as exc:
        raise ValueError("La fecha desde del ejercicio no es valida.") from exc

    periodo_inicial = fecha_desde.year * 100 + fecha_desde.month

    return [
        sumar_meses_periodo_yyyymm(periodo_inicial, desplazamiento)
        for desplazamiento in range(12)
    ]


def sumar_meses_periodo_yyyymm(periodo_yyyymm: int, meses: int) -> int:
    """Suma meses a un periodo YYYYMM manteniendo aritmetica mensual entera."""
    _validar_periodo_yyyymm(periodo_yyyymm)

    if isinstance(meses, bool) or not isinstance(meses, int):
        raise ValueError("La cantidad de meses debe ser entera.")

    anio = periodo_yyyymm // 100
    mes = periodo_yyyymm % 100
    total_meses = anio * 12 + (mes - 1) + meses

    if total_meses < 0:
        raise ValueError("El periodo resultante esta fuera de rango.")

    anio_resultado = total_meses // 12
    mes_resultado = total_meses % 12 + 1

    return anio_resultado * 100 + mes_resultado


def calcular_coeficiente_inflacion(
    indice_inicio_10000: int,
    indice_cierre_10000: int,
) -> int:
    """
    Calcula coeficiente cierre / inicio con enteros escalados.

    El resultado usa escala 12 y redondeo entero al mas cercano.
    """
    indice_inicio = _validar_entero_positivo(
        indice_inicio_10000,
        "indice_inicio_10000",
    )
    indice_cierre = _validar_entero_positivo(
        indice_cierre_10000,
        "indice_cierre_10000",
    )

    return (
        indice_cierre * _ESCALA_COEFICIENTE_INFLACION
        + indice_inicio // 2
    ) // indice_inicio


def preparar_coeficiente_inflacion_para_pantalla(
    coeficiente_inflacion: dict[str, Any],
) -> dict[str, Any]:
    """
    Agrega campos argentinos visibles al snapshot de coeficientes de inflacion.
    """
    coeficiente_pantalla = dict(coeficiente_inflacion)
    coeficiente_pantalla["periodo_argentina"] = (
        formatear_periodo_yyyymm_a_argentina(
            coeficiente_inflacion["periodo_yyyymm"]
        )
    )
    coeficiente_pantalla["indice_inicio_argentina"] = (
        formatear_entero_escala_a_decimal_argentino(
            coeficiente_inflacion["indice_inicio_10000"],
            4,
        )
    )
    coeficiente_pantalla["indice_cierre_periodo_argentina"] = (
        formatear_periodo_yyyymm_a_argentina(
            coeficiente_inflacion["indice_cierre_periodo_yyyymm"]
        )
    )
    coeficiente_pantalla["indice_cierre_argentina"] = (
        formatear_entero_escala_a_decimal_argentino(
            coeficiente_inflacion["indice_cierre_10000"],
            4,
        )
    )
    coeficiente_pantalla["coeficiente_argentina"] = (
        formatear_entero_escala_a_decimal_argentino(
            coeficiente_inflacion["coeficiente_1000000000000"],
            12,
        )
    )
    coeficiente_pantalla["calculado_en_argentina"] = (
        formatear_fecha_hora_sql_a_argentina(coeficiente_inflacion["calculado_en"])
        if coeficiente_inflacion.get("calculado_en")
        else None
    )

    return coeficiente_pantalla


def _obtener_ejercicio_contable_existente(
    ejercicio_contable_codigo: str,
) -> dict[str, Any]:
    codigo_normalizado = str(ejercicio_contable_codigo or "").strip()

    if not codigo_normalizado:
        raise ValueError("El codigo de ejercicio contable es obligatorio.")

    ejercicio_contable = obtener_ejercicio_contable_por_codigo(codigo_normalizado)

    if ejercicio_contable is None:
        raise ValueError("No existe el ejercicio contable informado.")

    return ejercicio_contable


def _validar_periodo_yyyymm(periodo_yyyymm: int) -> int:
    if isinstance(periodo_yyyymm, bool) or not isinstance(periodo_yyyymm, int):
        raise ValueError("El periodo YYYYMM debe ser entero.")

    mes = periodo_yyyymm % 100

    if periodo_yyyymm < 190001 or periodo_yyyymm > 299912:
        raise ValueError("El periodo YYYYMM esta fuera de rango.")

    if mes < 1 or mes > 12:
        raise ValueError("El mes del periodo YYYYMM debe estar entre 1 y 12.")

    return periodo_yyyymm


def _validar_entero_positivo(valor: int, nombre: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(f"{nombre} debe ser un entero positivo.")

    return valor
