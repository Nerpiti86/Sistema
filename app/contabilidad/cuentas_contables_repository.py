import re
import sqlite3
from datetime import datetime
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


def crear_cuenta_contable(datos_cuenta_contable: dict[str, Any]) -> dict[str, Any]:
    """
    Inserta un registro en cuentas_contables y devuelve la fila creada.

    Este repository ejecuta SQL directo. No resuelve reglas de formulario,
    rutas ni pantalla. La tabla mantiene sus propias restricciones, incluida
    la cuenta unica y la sumarizadora como codigo de cuenta padre.
    """
    cuenta_contable = _validar_cuenta_contable(datos_cuenta_contable["cuenta"])
    descripcion = _validar_texto_obligatorio(
        datos_cuenta_contable["descripcion"],
        "La descripcion de la cuenta contable es obligatoria.",
    )
    saldo_habitual = _validar_opcion_cuenta_contable(
        datos_cuenta_contable["saldo_habitual"],
        {"DEBE", "HABER"},
        "El saldo habitual de la cuenta contable es invalido.",
    )
    naturaleza = _validar_opcion_cuenta_contable(
        datos_cuenta_contable["naturaleza"],
        {"PATRIMONIAL", "RESULTADO"},
        "La naturaleza de la cuenta contable es invalida.",
    )
    imputable = _validar_booleano_cuenta_contable(
        datos_cuenta_contable["imputable"],
        "El valor imputable de la cuenta contable es invalido.",
    )
    monetaria = _validar_booleano_cuenta_contable(
        datos_cuenta_contable["monetaria"],
        "El valor monetario de la cuenta contable es invalido.",
    )
    sumarizadora = _normalizar_sumarizadora_cuenta_contable(
        datos_cuenta_contable.get("sumarizadora")
    )

    if sumarizadora == cuenta_contable:
        raise ValueError("La cuenta contable no puede sumarizarse a si misma.")

    db = get_db()

    try:
        with db:
            db.execute(
                """
                INSERT INTO cuentas_contables (
                    cuenta,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria,
                    sumarizadora
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cuenta_contable,
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria,
                    sumarizadora,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo crear la cuenta contable.") from exc

    cuenta_contable_creada = obtener_cuenta_contable_por_cuenta(cuenta_contable)

    if cuenta_contable_creada is None:
        raise ValueError("No se pudo recuperar la cuenta contable creada.")

    return cuenta_contable_creada


def actualizar_cuenta_contable_por_cuenta(
    cuenta_contable_codigo: str,
    datos_cuenta_contable: dict[str, Any],
) -> dict[str, Any]:
    """
    Actualiza campos mutables de una cuenta contable y devuelve la fila final.

    Este repository ejecuta SQL directo. No cambia el codigo de cuenta porque
    es identificador funcional usado por pantallas y futuros movimientos
    contables.
    """
    cuenta_contable_codigo_validado = _validar_cuenta_contable(cuenta_contable_codigo)

    if obtener_cuenta_contable_por_cuenta(cuenta_contable_codigo_validado) is None:
        raise ValueError("No existe la cuenta contable informada.")

    descripcion = _validar_texto_obligatorio(
        datos_cuenta_contable["descripcion"],
        "La descripcion de la cuenta contable es obligatoria.",
    )
    saldo_habitual = _validar_opcion_cuenta_contable(
        datos_cuenta_contable["saldo_habitual"],
        {"DEBE", "HABER"},
        "El saldo habitual de la cuenta contable es invalido.",
    )
    naturaleza = _validar_opcion_cuenta_contable(
        datos_cuenta_contable["naturaleza"],
        {"PATRIMONIAL", "RESULTADO"},
        "La naturaleza de la cuenta contable es invalida.",
    )
    imputable = _validar_booleano_cuenta_contable(
        datos_cuenta_contable["imputable"],
        "El valor imputable de la cuenta contable es invalido.",
    )
    monetaria = _validar_booleano_cuenta_contable(
        datos_cuenta_contable["monetaria"],
        "El valor monetario de la cuenta contable es invalido.",
    )
    sumarizadora = _normalizar_sumarizadora_cuenta_contable(
        datos_cuenta_contable.get("sumarizadora")
    )

    if sumarizadora == cuenta_contable_codigo_validado:
        raise ValueError("La cuenta contable no puede sumarizarse a si misma.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                UPDATE cuentas_contables
                SET
                    descripcion = ?,
                    saldo_habitual = ?,
                    naturaleza = ?,
                    imputable = ?,
                    monetaria = ?,
                    sumarizadora = ?,
                    actualizado_en = ?
                WHERE cuenta = ?
                """,
                (
                    descripcion,
                    saldo_habitual,
                    naturaleza,
                    imputable,
                    monetaria,
                    sumarizadora,
                    actualizado_en,
                    cuenta_contable_codigo_validado,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo actualizar la cuenta contable.") from exc

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar la cuenta contable.")

    cuenta_contable_actualizada = obtener_cuenta_contable_por_cuenta(
        cuenta_contable_codigo_validado
    )

    if cuenta_contable_actualizada is None:
        raise ValueError("No se pudo recuperar la cuenta contable actualizada.")

    return cuenta_contable_actualizada


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
          AND imputable = 1
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

    cuenta_contable["imputable"] = int(cuenta_contable["imputable"])
    cuenta_contable["monetaria"] = int(cuenta_contable["monetaria"])
    cuenta_contable["es_imputable"] = cuenta_contable["imputable"] == 1
    cuenta_contable["es_monetaria"] = cuenta_contable["monetaria"] == 1
    cuenta_contable["tiene_sumarizadora"] = cuenta_contable["sumarizadora"] is not None

    return cuenta_contable


def _normalizar_sumarizadora_cuenta_contable(sumarizadora: Any) -> str | None:
    """Normaliza sumarizadora nullable como codigo de cuenta padre."""
    if sumarizadora is None:
        return None

    sumarizadora_normalizada = str(sumarizadora).strip()

    if not sumarizadora_normalizada:
        return None

    return _validar_cuenta_contable(sumarizadora_normalizada)


def _validar_booleano_cuenta_contable(valor: Any, mensaje_error: str) -> int:
    """Valida booleano SQLite 0/1 del contrato de cuentas_contables."""
    if isinstance(valor, bool):
        return 1 if valor else 0

    if isinstance(valor, int) and valor in (0, 1):
        return valor

    valor_normalizado = str(valor or "").strip()

    if valor_normalizado in {"0", "1"}:
        return int(valor_normalizado)

    raise ValueError(mensaje_error)


def _validar_opcion_cuenta_contable(
    valor: Any,
    opciones_validas: set[str],
    mensaje_error: str,
) -> str:
    """Valida opciones cerradas del contrato de cuentas_contables."""
    valor_normalizado = str(valor or "").strip().upper()

    if valor_normalizado not in opciones_validas:
        raise ValueError(mensaje_error)

    return valor_normalizado


def _validar_texto_obligatorio(valor: Any, mensaje_error: str) -> str:
    """Valida texto obligatorio y devuelve version recortada."""
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        raise ValueError(mensaje_error)

    return valor_normalizado


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
