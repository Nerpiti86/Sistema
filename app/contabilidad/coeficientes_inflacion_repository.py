import sqlite3
from typing import Any

from app.db import get_db


_COLUMNAS_SELECT_INDICES_INFLACION = """
    id,
    periodo_yyyymm,
    indice_10000,
    creado_en,
    actualizado_en
"""

_COLUMNAS_SELECT_COEFICIENTES_INFLACION = """
    id,
    ejercicio_id,
    periodo_yyyymm,
    indice_inicio_10000,
    indice_cierre_periodo_yyyymm,
    indice_cierre_10000,
    coeficiente_1000000000000,
    calculado_en
"""


def guardar_indice_inflacion(
    periodo_yyyymm: int,
    indice_10000: int,
) -> dict[str, Any]:
    """
    Inserta o actualiza el indice de inflacion de un periodo mensual.

    Este repository ejecuta SQL directo y conserva los valores numericos como
    enteros escalados. No calcula coeficientes ni prepara datos de pantalla.
    """
    periodo_validado = _validar_periodo_yyyymm(periodo_yyyymm)
    indice_validado = _validar_entero_positivo(indice_10000, "indice_10000")

    db = get_db()

    try:
        with db:
            db.execute(
                """
                INSERT INTO indices_inflacion (
                    periodo_yyyymm,
                    indice_10000
                )
                VALUES (?, ?)
                ON CONFLICT(periodo_yyyymm) DO UPDATE SET
                    indice_10000 = excluded.indice_10000,
                    actualizado_en = CURRENT_TIMESTAMP
                """,
                (
                    periodo_validado,
                    indice_validado,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo guardar el indice de inflacion.") from exc

    indice_inflacion = obtener_indice_inflacion(periodo_validado)

    if indice_inflacion is None:
        raise ValueError("No se pudo recuperar el indice de inflacion guardado.")

    return indice_inflacion


def obtener_indice_inflacion(periodo_yyyymm: int) -> dict[str, Any] | None:
    """Devuelve el indice de inflacion de un periodo, o None si no existe."""
    periodo_validado = _validar_periodo_yyyymm(periodo_yyyymm)

    fila_indice = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_INDICES_INFLACION}
        FROM indices_inflacion
        WHERE periodo_yyyymm = ?
        LIMIT 1
        """,
        (periodo_validado,),
    ).fetchone()

    if fila_indice is None:
        return None

    return _normalizar_fila(fila_indice)


def obtener_ultimo_indice_inflacion() -> dict[str, Any] | None:
    """Devuelve el ultimo indice cargado por periodo mensual."""
    fila_indice = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_INDICES_INFLACION}
        FROM indices_inflacion
        ORDER BY periodo_yyyymm DESC
        LIMIT 1
        """
    ).fetchone()

    if fila_indice is None:
        return None

    return _normalizar_fila(fila_indice)


def listar_indices_inflacion() -> list[dict[str, Any]]:
    """Devuelve los indices de inflacion ordenados por periodo."""
    filas_indices = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_INDICES_INFLACION}
        FROM indices_inflacion
        ORDER BY periodo_yyyymm
        """
    ).fetchall()

    return [_normalizar_fila(fila_indice) for fila_indice in filas_indices]


def reemplazar_coeficientes_inflacion_ejercicio(
    ejercicio_id: int,
    coeficientes_inflacion: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Reemplaza los coeficientes persistidos de un ejercicio contable.

    La cantidad esperada de periodos y el calculo del coeficiente pertenecen al
    service. El repository solo valida enteros escalados y persiste el snapshot.
    """
    ejercicio_id_validado = _validar_entero_positivo(ejercicio_id, "ejercicio_id")

    if not isinstance(coeficientes_inflacion, list) or not coeficientes_inflacion:
        raise ValueError("Debe informar coeficientes de inflacion.")

    coeficientes_validados = [
        _validar_coeficiente_inflacion(coeficiente_inflacion)
        for coeficiente_inflacion in coeficientes_inflacion
    ]

    db = get_db()

    try:
        with db:
            db.execute(
                """
                DELETE FROM ejercicios_coeficientes_inflacion
                WHERE ejercicio_id = ?
                """,
                (ejercicio_id_validado,),
            )

            db.executemany(
                """
                INSERT INTO ejercicios_coeficientes_inflacion (
                    ejercicio_id,
                    periodo_yyyymm,
                    indice_inicio_10000,
                    indice_cierre_periodo_yyyymm,
                    indice_cierre_10000,
                    coeficiente_1000000000000
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        ejercicio_id_validado,
                        coeficiente["periodo_yyyymm"],
                        coeficiente["indice_inicio_10000"],
                        coeficiente["indice_cierre_periodo_yyyymm"],
                        coeficiente["indice_cierre_10000"],
                        coeficiente["coeficiente_1000000000000"],
                    )
                    for coeficiente in coeficientes_validados
                ],
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudieron guardar los coeficientes de inflacion."
        ) from exc

    return listar_coeficientes_inflacion_por_ejercicio_id(ejercicio_id_validado)


def listar_coeficientes_inflacion_por_ejercicio_id(
    ejercicio_id: int,
) -> list[dict[str, Any]]:
    """Devuelve coeficientes de inflacion de un ejercicio ordenados por periodo."""
    ejercicio_id_validado = _validar_entero_positivo(ejercicio_id, "ejercicio_id")

    filas_coeficientes = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_COEFICIENTES_INFLACION}
        FROM ejercicios_coeficientes_inflacion
        WHERE ejercicio_id = ?
        ORDER BY periodo_yyyymm
        """,
        (ejercicio_id_validado,),
    ).fetchall()

    return [
        _normalizar_fila(fila_coeficiente)
        for fila_coeficiente in filas_coeficientes
    ]


def _validar_coeficiente_inflacion(
    coeficiente_inflacion: dict[str, Any],
) -> dict[str, int]:
    if not isinstance(coeficiente_inflacion, dict):
        raise ValueError("Cada coeficiente de inflacion debe ser un diccionario.")

    return {
        "periodo_yyyymm": _validar_periodo_yyyymm(
            coeficiente_inflacion.get("periodo_yyyymm")
        ),
        "indice_inicio_10000": _validar_entero_positivo(
            coeficiente_inflacion.get("indice_inicio_10000"),
            "indice_inicio_10000",
        ),
        "indice_cierre_periodo_yyyymm": _validar_periodo_yyyymm(
            coeficiente_inflacion.get("indice_cierre_periodo_yyyymm")
        ),
        "indice_cierre_10000": _validar_entero_positivo(
            coeficiente_inflacion.get("indice_cierre_10000"),
            "indice_cierre_10000",
        ),
        "coeficiente_1000000000000": _validar_entero_positivo(
            coeficiente_inflacion.get("coeficiente_1000000000000"),
            "coeficiente_1000000000000",
        ),
    }


def _validar_periodo_yyyymm(periodo_yyyymm: int) -> int:
    if isinstance(periodo_yyyymm, bool) or not isinstance(periodo_yyyymm, int):
        raise ValueError("El periodo YYYYMM debe ser un entero.")

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


def _normalizar_fila(fila) -> dict[str, Any]:
    return dict(fila)
