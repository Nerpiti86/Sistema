from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_MONEDAS = """
    id,
    codigo,
    nombre,
    simbolo,
    decimales,
    activa,
    orden,
    creado_en,
    actualizado_en
"""


def listar_monedas() -> list[dict[str, Any]]:
    """
    Devuelve monedas ordenadas para uso transversal.

    La tabla monedas es un maestro chico compartido por gestion, contabilidad,
    tesoreria y reportes. No corresponde paginarla en esta etapa.
    """
    filas_monedas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS}
        FROM monedas
        ORDER BY orden, codigo
        """
    ).fetchall()

    return [_normalizar_fila_moneda(fila_moneda) for fila_moneda in filas_monedas]


def listar_monedas_activas() -> list[dict[str, Any]]:
    """Devuelve monedas activas ordenadas para selects y operaciones."""
    filas_monedas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS}
        FROM monedas
        WHERE activa = 1
        ORDER BY orden, codigo
        """
    ).fetchall()

    return [_normalizar_fila_moneda(fila_moneda) for fila_moneda in filas_monedas]


def obtener_moneda_por_codigo(codigo_moneda: Any) -> dict[str, Any] | None:
    """Devuelve una moneda por codigo, o None si no existe."""
    codigo_moneda_validado = _validar_codigo_moneda(codigo_moneda)

    fila_moneda = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS}
        FROM monedas
        WHERE codigo = ?
        LIMIT 1
        """,
        (codigo_moneda_validado,),
    ).fetchone()

    if fila_moneda is None:
        return None

    return _normalizar_fila_moneda(fila_moneda)


def validar_moneda_activa(codigo_moneda: Any) -> bool:
    """Valida que una moneda exista y este activa."""
    codigo_moneda_validado = _validar_codigo_moneda(codigo_moneda)

    fila_moneda = get_db().execute(
        """
        SELECT 1
        FROM monedas
        WHERE codigo = ?
          AND activa = 1
        LIMIT 1
        """,
        (codigo_moneda_validado,),
    ).fetchone()

    if fila_moneda is None:
        raise ValueError("La moneda no existe o no esta activa.")

    return True


def _normalizar_fila_moneda(fila_moneda) -> dict[str, Any]:
    """Convierte una fila SQLite de monedas en dict explicito."""
    moneda = dict(fila_moneda)

    moneda["decimales"] = int(moneda["decimales"])
    moneda["activa"] = int(moneda["activa"])
    moneda["orden"] = int(moneda["orden"])
    moneda["esta_activa"] = moneda["activa"] == 1
    moneda["descripcion_select"] = (
        f"{moneda['codigo']} - {moneda['nombre']}"
    )

    return moneda


def _validar_codigo_moneda(codigo_moneda: Any) -> str:
    """Valida y normaliza codigo de moneda ISO de tres letras."""
    codigo_moneda_validado = str(codigo_moneda or "").strip().upper()

    if not codigo_moneda_validado:
        raise ValueError("El codigo de moneda es obligatorio.")

    if len(codigo_moneda_validado) != 3 or not codigo_moneda_validado.isalpha():
        raise ValueError("El codigo de moneda debe tener formato AAA.")

    return codigo_moneda_validado
