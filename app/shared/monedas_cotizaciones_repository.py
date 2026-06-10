import re
import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db
from app.shared.monedas_repository import validar_moneda_activa

_COLUMNAS_SELECT_MONEDAS_COTIZACIONES = """
    id,
    moneda_origen_codigo,
    moneda_destino_codigo,
    fecha,
    tipo,
    cotizacion_1000000,
    fuente,
    observaciones,
    creado_en,
    actualizado_en
"""

_TIPOS_COTIZACION_VALIDOS = {"COMPRA", "VENTA", "CIERRE", "PROMEDIO"}
_PATRON_FECHA_ISO_COTIZACION = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def listar_monedas_cotizaciones_recientes(
    limite: int = 100,
) -> list[dict[str, Any]]:
    """
    Devuelve cotizaciones recientes con limite explicito.

    La tabla puede crecer por fecha, por eso no se devuelve sin limite.
    """
    limite_validado = _validar_limite_cotizaciones(limite)

    filas_cotizaciones = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS_COTIZACIONES}
        FROM monedas_cotizaciones
        ORDER BY fecha DESC, id DESC
        LIMIT ?
        """,
        (limite_validado,),
    ).fetchall()

    return [
        _normalizar_fila_moneda_cotizacion(fila_cotizacion)
        for fila_cotizacion in filas_cotizaciones
    ]


def listar_monedas_cotizaciones_por_par(
    moneda_origen_codigo: Any,
    moneda_destino_codigo: Any,
    tipo: Any = "CIERRE",
    limite: int = 100,
) -> list[dict[str, Any]]:
    """Devuelve cotizaciones de un par ordenadas desde la mas reciente."""
    moneda_origen_validada = _validar_codigo_moneda_cotizacion(
        moneda_origen_codigo,
        "La moneda origen es obligatoria.",
    )
    moneda_destino_validada = _validar_codigo_moneda_cotizacion(
        moneda_destino_codigo,
        "La moneda destino es obligatoria.",
    )
    tipo_validado = _validar_tipo_cotizacion(tipo)
    limite_validado = _validar_limite_cotizaciones(limite)

    filas_cotizaciones = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS_COTIZACIONES}
        FROM monedas_cotizaciones
        WHERE moneda_origen_codigo = ?
          AND moneda_destino_codigo = ?
          AND tipo = ?
        ORDER BY fecha DESC, id DESC
        LIMIT ?
        """,
        (
            moneda_origen_validada,
            moneda_destino_validada,
            tipo_validado,
            limite_validado,
        ),
    ).fetchall()

    return [
        _normalizar_fila_moneda_cotizacion(fila_cotizacion)
        for fila_cotizacion in filas_cotizaciones
    ]


def obtener_moneda_cotizacion(
    moneda_origen_codigo: Any,
    moneda_destino_codigo: Any,
    fecha: Any,
    tipo: Any = "CIERRE",
) -> dict[str, Any] | None:
    """Devuelve una cotizacion puntual por par, fecha y tipo."""
    moneda_origen_validada = _validar_codigo_moneda_cotizacion(
        moneda_origen_codigo,
        "La moneda origen es obligatoria.",
    )
    moneda_destino_validada = _validar_codigo_moneda_cotizacion(
        moneda_destino_codigo,
        "La moneda destino es obligatoria.",
    )
    fecha_validada = _validar_fecha_iso_cotizacion(fecha)
    tipo_validado = _validar_tipo_cotizacion(tipo)

    fila_cotizacion = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS_COTIZACIONES}
        FROM monedas_cotizaciones
        WHERE moneda_origen_codigo = ?
          AND moneda_destino_codigo = ?
          AND fecha = ?
          AND tipo = ?
        LIMIT 1
        """,
        (
            moneda_origen_validada,
            moneda_destino_validada,
            fecha_validada,
            tipo_validado,
        ),
    ).fetchone()

    if fila_cotizacion is None:
        return None

    return _normalizar_fila_moneda_cotizacion(fila_cotizacion)


def obtener_ultima_moneda_cotizacion(
    moneda_origen_codigo: Any,
    moneda_destino_codigo: Any,
    tipo: Any = "CIERRE",
    fecha_hasta: Any | None = None,
) -> dict[str, Any] | None:
    """Devuelve la ultima cotizacion disponible de un par."""
    moneda_origen_validada = _validar_codigo_moneda_cotizacion(
        moneda_origen_codigo,
        "La moneda origen es obligatoria.",
    )
    moneda_destino_validada = _validar_codigo_moneda_cotizacion(
        moneda_destino_codigo,
        "La moneda destino es obligatoria.",
    )
    tipo_validado = _validar_tipo_cotizacion(tipo)

    parametros: list[Any] = [
        moneda_origen_validada,
        moneda_destino_validada,
        tipo_validado,
    ]
    condicion_fecha = ""

    if fecha_hasta is not None:
        fecha_hasta_validada = _validar_fecha_iso_cotizacion(fecha_hasta)
        condicion_fecha = "AND fecha <= ?"
        parametros.append(fecha_hasta_validada)

    fila_cotizacion = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MONEDAS_COTIZACIONES}
        FROM monedas_cotizaciones
        WHERE moneda_origen_codigo = ?
          AND moneda_destino_codigo = ?
          AND tipo = ?
          {condicion_fecha}
        ORDER BY fecha DESC, id DESC
        LIMIT 1
        """,
        tuple(parametros),
    ).fetchone()

    if fila_cotizacion is None:
        return None

    return _normalizar_fila_moneda_cotizacion(fila_cotizacion)


def crear_moneda_cotizacion(
    datos_cotizacion: dict[str, Any],
) -> dict[str, Any]:
    """
    Inserta una cotizacion de moneda y devuelve la fila creada.

    Este repository ejecuta SQL directo. No resuelve reglas de pantalla.
    """
    moneda_origen_codigo = _validar_codigo_moneda_cotizacion(
        datos_cotizacion["moneda_origen_codigo"],
        "La moneda origen es obligatoria.",
    )
    moneda_destino_codigo = _validar_codigo_moneda_cotizacion(
        datos_cotizacion["moneda_destino_codigo"],
        "La moneda destino es obligatoria.",
    )

    if moneda_origen_codigo == moneda_destino_codigo:
        raise ValueError("La moneda origen no puede ser igual a la moneda destino.")

    validar_moneda_activa(moneda_origen_codigo)
    validar_moneda_activa(moneda_destino_codigo)

    fecha = _validar_fecha_iso_cotizacion(datos_cotizacion["fecha"])
    tipo = _validar_tipo_cotizacion(datos_cotizacion.get("tipo", "CIERRE"))
    cotizacion_1000000 = _validar_cotizacion_1000000(
        datos_cotizacion["cotizacion_1000000"]
    )
    fuente = _normalizar_texto_opcional(datos_cotizacion.get("fuente"))
    observaciones = _normalizar_texto_opcional(
        datos_cotizacion.get("observaciones")
    )
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            db.execute(
                """
                INSERT INTO monedas_cotizaciones (
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    fecha,
                    tipo,
                    cotizacion_1000000,
                    fuente,
                    observaciones,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    moneda_origen_codigo,
                    moneda_destino_codigo,
                    fecha,
                    tipo,
                    cotizacion_1000000,
                    fuente,
                    observaciones,
                    creado_en,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo crear la cotizacion de moneda.") from exc

    cotizacion_creada = obtener_moneda_cotizacion(
        moneda_origen_codigo,
        moneda_destino_codigo,
        fecha,
        tipo,
    )

    if cotizacion_creada is None:
        raise ValueError("No se pudo recuperar la cotizacion de moneda creada.")

    return cotizacion_creada


def _normalizar_fila_moneda_cotizacion(fila_cotizacion) -> dict[str, Any]:
    """Convierte una fila SQLite de monedas_cotizaciones en dict explicito."""
    cotizacion = dict(fila_cotizacion)

    cotizacion["cotizacion_1000000"] = int(cotizacion["cotizacion_1000000"])
    cotizacion["par_codigo"] = (
        f"{cotizacion['moneda_origen_codigo']}/"
        f"{cotizacion['moneda_destino_codigo']}"
    )

    return cotizacion


def _validar_codigo_moneda_cotizacion(
    codigo_moneda: Any,
    mensaje_obligatorio: str,
) -> str:
    """Valida y normaliza codigo de moneda para cotizaciones."""
    codigo_moneda_validado = str(codigo_moneda or "").strip().upper()

    if not codigo_moneda_validado:
        raise ValueError(mensaje_obligatorio)

    if len(codigo_moneda_validado) != 3 or not codigo_moneda_validado.isalpha():
        raise ValueError("El codigo de moneda debe tener formato AAA.")

    return codigo_moneda_validado


def _validar_fecha_iso_cotizacion(fecha: Any) -> str:
    """Valida fecha ISO YYYY-MM-DD para cotizaciones."""
    fecha_validada = str(fecha or "").strip()

    if not _PATRON_FECHA_ISO_COTIZACION.match(fecha_validada):
        raise ValueError("La fecha de cotizacion debe tener formato YYYY-MM-DD.")

    try:
        datetime.strptime(fecha_validada, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("La fecha de cotizacion debe ser una fecha valida.") from exc

    return fecha_validada


def _validar_tipo_cotizacion(tipo: Any) -> str:
    """Valida tipo cerrado de cotizacion."""
    tipo_validado = str(tipo or "").strip().upper()

    if tipo_validado not in _TIPOS_COTIZACION_VALIDOS:
        raise ValueError("El tipo de cotizacion es invalido.")

    return tipo_validado


def _validar_cotizacion_1000000(cotizacion_1000000: Any) -> int:
    """Valida cotizacion escalada como entero positivo."""
    if isinstance(cotizacion_1000000, bool):
        raise ValueError("La cotizacion debe ser un entero positivo.")

    try:
        cotizacion_validada = int(cotizacion_1000000)
    except (TypeError, ValueError) as exc:
        raise ValueError("La cotizacion debe ser un entero positivo.") from exc

    if cotizacion_validada <= 0:
        raise ValueError("La cotizacion debe ser mayor a cero.")

    return cotizacion_validada


def _validar_limite_cotizaciones(limite: Any) -> int:
    """Valida limite de filas para consultas de cotizaciones."""
    if isinstance(limite, bool):
        raise ValueError("El limite de cotizaciones es invalido.")

    try:
        limite_validado = int(limite)
    except (TypeError, ValueError) as exc:
        raise ValueError("El limite de cotizaciones es invalido.") from exc

    if limite_validado < 1 or limite_validado > 500:
        raise ValueError("El limite de cotizaciones debe estar entre 1 y 500.")

    return limite_validado


def _normalizar_texto_opcional(valor: Any) -> str | None:
    """Normaliza texto opcional nullable."""
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return valor_normalizado
