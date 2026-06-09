import re
from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_CUENTAS_CONTABLES = """
    id,
    cuenta,
    descripcion,
    saldo_habitual,
    naturaleza,
    imputable,
    monetaria,
    sumarizadora,
    creado_en,
    actualizado_en
"""

_PATRON_CUENTA_CONTABLE = re.compile(r"^\d\.\d\.\d{2}\.\d{2}\.\d{3}$")


def listar_cuentas_contables() -> list[dict[str, Any]]:
    """
    Devuelve cuentas contables ordenadas por codigo de cuenta.

    La tabla cuentas_contables es un maestro contable controlado. Para tablas
    operativas grandes, los repositories deben paginar o agregar en SQL.
    """
    filas_cuentas_contables = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CUENTAS_CONTABLES}
        FROM cuentas_contables
        ORDER BY cuenta
        """
    ).fetchall()

    return [
        _normalizar_fila_cuenta_contable(fila_cuenta_contable)
        for fila_cuenta_contable in filas_cuentas_contables
    ]


def obtener_cuenta_contable_por_cuenta(
    cuenta_contable: str,
) -> dict[str, Any] | None:
    """Devuelve una cuenta contable por codigo, o None si no existe."""
    cuenta_contable_validada = _validar_cuenta_contable(cuenta_contable)

    fila_cuenta_contable = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CUENTAS_CONTABLES}
        FROM cuentas_contables
        WHERE cuenta = ?
        LIMIT 1
        """,
        (cuenta_contable_validada,),
    ).fetchone()

    if fila_cuenta_contable is None:
        return None

    return _normalizar_fila_cuenta_contable(fila_cuenta_contable)


def listar_cuentas_contables_por_sumarizadora(
    cuenta_sumarizadora: str,
) -> list[dict[str, Any]]:
    """Devuelve hijas directas de una cuenta sumarizadora."""
    cuenta_sumarizadora_validada = _validar_cuenta_contable(cuenta_sumarizadora)

    filas_cuentas_contables = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CUENTAS_CONTABLES}
        FROM cuentas_contables
        WHERE sumarizadora = ?
        ORDER BY cuenta
        """,
        (cuenta_sumarizadora_validada,),
    ).fetchall()

    return [
        _normalizar_fila_cuenta_contable(fila_cuenta_contable)
        for fila_cuenta_contable in filas_cuentas_contables
    ]


def validar_cuenta_contable_imputable(cuenta_contable: str) -> bool:
    """Valida que una cuenta exista y permita imputacion contable."""
    cuenta_contable_validada = _validar_cuenta_contable(cuenta_contable)

    fila_cuenta_contable = get_db().execute(
        """
        SELECT 1
        FROM cuentas_contables
        WHERE cuenta = ?
          AND imputable = 'SI'
        LIMIT 1
        """,
        (cuenta_contable_validada,),
    ).fetchone()

    if fila_cuenta_contable is None:
        raise ValueError("La cuenta contable no existe o no es imputable.")

    return True


def _normalizar_fila_cuenta_contable(fila_cuenta_contable) -> dict[str, Any]:
    """Convierte una fila SQLite de cuentas_contables en dict explicito."""
    cuenta_contable = dict(fila_cuenta_contable)

    cuenta_contable["es_imputable"] = cuenta_contable["imputable"] == "SI"
    cuenta_contable["es_monetaria"] = cuenta_contable["monetaria"] == "SI"
    cuenta_contable["tiene_sumarizadora"] = cuenta_contable["sumarizadora"] is not None

    return cuenta_contable


def _validar_cuenta_contable(cuenta_contable: str) -> str:
    """Valida y normaliza codigo de cuenta contable."""
    if not isinstance(cuenta_contable, str):
        raise ValueError("La cuenta contable es obligatoria.")

    cuenta_contable_validada = cuenta_contable.strip()

    if not cuenta_contable_validada:
        raise ValueError("La cuenta contable es obligatoria.")

    if not _PATRON_CUENTA_CONTABLE.match(cuenta_contable_validada):
        raise ValueError("La cuenta contable debe tener formato 9.9.99.99.999.")

    return cuenta_contable_validada
