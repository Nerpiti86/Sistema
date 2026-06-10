import re
import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_EJERCICIOS_CONTABLES = """
    id,
    codigo,
    nombre,
    fecha_desde,
    fecha_hasta,
    estado,
    activo,
    creado_en,
    actualizado_en,
    fase_cierre,
    bloqueado,
    bloqueado_en,
    observaciones_cierre,
    es_primer_ejercicio
"""

_PATRON_FECHA_ISO_EJERCICIO_CONTABLE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def listar_ejercicios_contables() -> list[dict[str, Any]]:
    """
    Devuelve ejercicios contables ordenados por fecha.

    La tabla ejercicios_contables es una tabla chica de contexto contable.
    Por eso este listado puede devolver todos los ejercicios. Para tablas
    operativas grandes, los repositories deben paginar o agregar en SQL.
    """
    filas_ejercicios_contables = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_EJERCICIOS_CONTABLES}
        FROM ejercicios_contables
        ORDER BY fecha_desde, codigo
        """
    ).fetchall()

    return [
        _normalizar_fila_ejercicio_contable(fila_ejercicio_contable)
        for fila_ejercicio_contable in filas_ejercicios_contables
    ]


def obtener_ejercicio_contable_activo() -> dict[str, Any]:
    """
    Devuelve el unico ejercicio contable activo.

    Usa LIMIT 2 para detectar inconsistencia sin cargar toda la tabla.
    """
    ejercicios_contables_activos = _obtener_hasta_dos_ejercicios_contables_por_sql(
        f"""
        SELECT {_COLUMNAS_SELECT_EJERCICIOS_CONTABLES}
        FROM ejercicios_contables
        WHERE activo = 1
        ORDER BY fecha_desde DESC, codigo DESC
        LIMIT 2
        """,
        (),
    )

    if len(ejercicios_contables_activos) != 1:
        raise ValueError("Debe existir un unico ejercicio contable activo.")

    return ejercicios_contables_activos[0]


def obtener_ejercicio_contable_por_codigo(
    ejercicio_contable_codigo: str,
) -> dict[str, Any] | None:
    """Devuelve un ejercicio contable por codigo, o None si no existe."""
    ejercicio_contable_codigo_validado = _validar_codigo_ejercicio_contable(
        ejercicio_contable_codigo
    )

    fila_ejercicio_contable = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_EJERCICIOS_CONTABLES}
        FROM ejercicios_contables
        WHERE codigo = ?
        LIMIT 1
        """,
        (ejercicio_contable_codigo_validado,),
    ).fetchone()

    if fila_ejercicio_contable is None:
        return None

    return _normalizar_fila_ejercicio_contable(fila_ejercicio_contable)


def obtener_ejercicio_contable_por_fecha(
    fecha_operacion_iso: str,
) -> dict[str, Any] | None:
    """
    Devuelve el ejercicio contable que contiene la fecha informada.

    Usa LIMIT 2 para detectar rangos superpuestos sin cargar todos los datos.
    """
    fecha_operacion_iso_validada = _validar_fecha_iso_ejercicio_contable(
        fecha_operacion_iso
    )

    ejercicios_contables_en_fecha = _obtener_hasta_dos_ejercicios_contables_por_sql(
        f"""
        SELECT {_COLUMNAS_SELECT_EJERCICIOS_CONTABLES}
        FROM ejercicios_contables
        WHERE fecha_desde <= ?
          AND fecha_hasta >= ?
        ORDER BY activo DESC, fecha_desde DESC, codigo DESC
        LIMIT 2
        """,
        (
            fecha_operacion_iso_validada,
            fecha_operacion_iso_validada,
        ),
    )

    if len(ejercicios_contables_en_fecha) > 1:
        raise ValueError("Existe mas de un ejercicio contable para la fecha informada.")

    if not ejercicios_contables_en_fecha:
        return None

    return ejercicios_contables_en_fecha[0]



def crear_ejercicio_contable(
    datos_ejercicio_contable: dict[str, Any],
) -> dict[str, Any]:
    """
    Inserta un registro en ejercicios_contables y devuelve la fila creada.

    Este repository ejecuta SQL directo. No resuelve reglas de formulario,
    rutas ni pantalla. La tabla mantiene sus propias restricciones, incluido
    el indice unico de activo.
    """
    ejercicio_contable_codigo = _validar_codigo_ejercicio_contable(
        datos_ejercicio_contable["codigo"]
    )
    ejercicio_contable_nombre = _validar_nombre_ejercicio_contable(
        datos_ejercicio_contable["nombre"]
    )
    ejercicio_contable_fecha_desde = _validar_fecha_iso_ejercicio_contable(
        datos_ejercicio_contable["fecha_desde"]
    )
    ejercicio_contable_fecha_hasta = _validar_fecha_iso_ejercicio_contable(
        datos_ejercicio_contable["fecha_hasta"]
    )

    if ejercicio_contable_fecha_hasta < ejercicio_contable_fecha_desde:
        raise ValueError("La fecha hasta no puede ser anterior a la fecha desde.")

    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            db.execute(
                """
                INSERT INTO ejercicios_contables (
                    codigo,
                    nombre,
                    fecha_desde,
                    fecha_hasta,
                    estado,
                    activo,
                    fase_cierre,
                    bloqueado,
                    bloqueado_en,
                    observaciones_cierre,
                    es_primer_ejercicio,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ejercicio_contable_codigo,
                    ejercicio_contable_nombre,
                    ejercicio_contable_fecha_desde,
                    ejercicio_contable_fecha_hasta,
                    datos_ejercicio_contable["estado"],
                    int(datos_ejercicio_contable["activo"]),
                    datos_ejercicio_contable["fase_cierre"],
                    int(datos_ejercicio_contable["bloqueado"]),
                    datos_ejercicio_contable["bloqueado_en"],
                    datos_ejercicio_contable["observaciones_cierre"],
                    int(datos_ejercicio_contable["es_primer_ejercicio"]),
                    creado_en,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo crear el ejercicio contable.") from exc

    ejercicio_contable_creado = obtener_ejercicio_contable_por_codigo(
        ejercicio_contable_codigo
    )

    if ejercicio_contable_creado is None:
        raise ValueError("No se pudo recuperar el ejercicio contable creado.")

    return ejercicio_contable_creado


def actualizar_ejercicio_contable_por_codigo(
    ejercicio_contable_codigo: str,
    datos_ejercicio_contable: dict[str, Any],
) -> dict[str, Any]:
    """
    Actualiza campos mutables de un ejercicio contable y devuelve la fila final.

    Este repository ejecuta SQL directo. No cambia el codigo del ejercicio
    porque el codigo es identificador funcional usado por pantallas y futuros
    movimientos contables.
    """
    ejercicio_contable_codigo_validado = _validar_codigo_ejercicio_contable(
        ejercicio_contable_codigo
    )

    if obtener_ejercicio_contable_por_codigo(ejercicio_contable_codigo_validado) is None:
        raise ValueError("No existe el ejercicio contable informado.")

    ejercicio_contable_nombre = _validar_nombre_ejercicio_contable(
        datos_ejercicio_contable["nombre"]
    )
    ejercicio_contable_fecha_desde = _validar_fecha_iso_ejercicio_contable(
        datos_ejercicio_contable["fecha_desde"]
    )
    ejercicio_contable_fecha_hasta = _validar_fecha_iso_ejercicio_contable(
        datos_ejercicio_contable["fecha_hasta"]
    )

    if ejercicio_contable_fecha_hasta < ejercicio_contable_fecha_desde:
        raise ValueError("La fecha hasta no puede ser anterior a la fecha desde.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                UPDATE ejercicios_contables
                SET
                    nombre = ?,
                    fecha_desde = ?,
                    fecha_hasta = ?,
                    estado = ?,
                    activo = ?,
                    actualizado_en = ?,
                    fase_cierre = ?,
                    bloqueado = ?,
                    bloqueado_en = ?,
                    observaciones_cierre = ?,
                    es_primer_ejercicio = ?
                WHERE codigo = ?
                """,
                (
                    ejercicio_contable_nombre,
                    ejercicio_contable_fecha_desde,
                    ejercicio_contable_fecha_hasta,
                    datos_ejercicio_contable["estado"],
                    int(datos_ejercicio_contable["activo"]),
                    actualizado_en,
                    datos_ejercicio_contable["fase_cierre"],
                    int(datos_ejercicio_contable["bloqueado"]),
                    datos_ejercicio_contable["bloqueado_en"],
                    datos_ejercicio_contable["observaciones_cierre"],
                    int(datos_ejercicio_contable["es_primer_ejercicio"]),
                    ejercicio_contable_codigo_validado,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo actualizar el ejercicio contable.") from exc

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el ejercicio contable.")

    ejercicio_contable_actualizado = obtener_ejercicio_contable_por_codigo(
        ejercicio_contable_codigo_validado
    )

    if ejercicio_contable_actualizado is None:
        raise ValueError("No se pudo recuperar el ejercicio contable actualizado.")

    return ejercicio_contable_actualizado


def validar_fecha_dentro_de_ejercicio_contable(
    fecha_operacion_iso: str,
    ejercicio_contable_codigo: str,
) -> bool:
    """Valida que una fecha pertenezca al rango del ejercicio contable."""
    fecha_operacion_iso_validada = _validar_fecha_iso_ejercicio_contable(
        fecha_operacion_iso
    )
    ejercicio_contable_codigo_validado = _validar_codigo_ejercicio_contable(
        ejercicio_contable_codigo
    )

    fila_validacion_fecha_ejercicio_contable = get_db().execute(
        """
        SELECT 1
        FROM ejercicios_contables
        WHERE codigo = ?
          AND fecha_desde <= ?
          AND fecha_hasta >= ?
        LIMIT 1
        """,
        (
            ejercicio_contable_codigo_validado,
            fecha_operacion_iso_validada,
            fecha_operacion_iso_validada,
        ),
    ).fetchone()

    if fila_validacion_fecha_ejercicio_contable is None:
        raise ValueError("La fecha no pertenece al ejercicio contable informado.")

    return True


def validar_ejercicio_contable_operable(ejercicio_contable_codigo: str) -> bool:
    """
    Valida que el ejercicio contable permita operaciones.

    Condicion operable:
    - estado ABIERTO
    - fase_cierre ABIERTO o EN_CIERRE
    - bloqueado 0
    """
    ejercicio_contable_codigo_validado = _validar_codigo_ejercicio_contable(
        ejercicio_contable_codigo
    )

    fila_ejercicio_contable_operable = get_db().execute(
        """
        SELECT 1
        FROM ejercicios_contables
        WHERE codigo = ?
          AND estado = 'ABIERTO'
          AND fase_cierre IN ('ABIERTO', 'EN_CIERRE')
          AND bloqueado = 0
        LIMIT 1
        """,
        (ejercicio_contable_codigo_validado,),
    ).fetchone()

    if fila_ejercicio_contable_operable is None:
        raise ValueError("El ejercicio contable no permite operaciones.")

    return True


def _obtener_hasta_dos_ejercicios_contables_por_sql(
    sql_ejercicios_contables: str,
    parametros_ejercicios_contables: tuple[Any, ...],
) -> list[dict[str, Any]]:
    """
    Ejecuta una consulta que debe devolver cero, uno o dos ejercicios.

    El limite de dos filas permite detectar ambiguedad con bajo consumo de RAM.
    """
    cursor_ejercicios_contables = get_db().execute(
        sql_ejercicios_contables,
        parametros_ejercicios_contables,
    )

    filas_ejercicios_contables = cursor_ejercicios_contables.fetchmany(2)

    return [
        _normalizar_fila_ejercicio_contable(fila_ejercicio_contable)
        for fila_ejercicio_contable in filas_ejercicios_contables
    ]


def _normalizar_fila_ejercicio_contable(
    fila_ejercicio_contable,
) -> dict[str, Any]:
    """Convierte una fila SQLite de ejercicios_contables en dict explicito."""
    ejercicio_contable = dict(fila_ejercicio_contable)

    ejercicio_contable["estado_codigo"] = ejercicio_contable["estado"]
    ejercicio_contable["fase_cierre_codigo"] = ejercicio_contable["fase_cierre"]
    ejercicio_contable["es_activo"] = bool(ejercicio_contable["activo"])
    ejercicio_contable["esta_bloqueado"] = bool(ejercicio_contable["bloqueado"])
    ejercicio_contable["es_primer_ejercicio_bool"] = bool(
        ejercicio_contable["es_primer_ejercicio"]
    )

    return ejercicio_contable


def _validar_codigo_ejercicio_contable(
    ejercicio_contable_codigo: str,
) -> str:
    """Valida y normaliza codigo de ejercicio contable."""
    if not isinstance(ejercicio_contable_codigo, str):
        raise ValueError("El codigo de ejercicio contable es obligatorio.")

    ejercicio_contable_codigo_validado = ejercicio_contable_codigo.strip()

    if not ejercicio_contable_codigo_validado:
        raise ValueError("El codigo de ejercicio contable es obligatorio.")

    return ejercicio_contable_codigo_validado



def _validar_nombre_ejercicio_contable(
    ejercicio_contable_nombre: str,
) -> str:
    """Valida y normaliza nombre de ejercicio contable."""
    if not isinstance(ejercicio_contable_nombre, str):
        raise ValueError("El nombre de ejercicio contable es obligatorio.")

    ejercicio_contable_nombre_validado = ejercicio_contable_nombre.strip()

    if not ejercicio_contable_nombre_validado:
        raise ValueError("El nombre de ejercicio contable es obligatorio.")

    return ejercicio_contable_nombre_validado


def _validar_fecha_iso_ejercicio_contable(fecha_operacion_iso: str) -> str:
    """Valida fecha ISO YYYY-MM-DD para ejercicios contables."""
    if not isinstance(fecha_operacion_iso, str):
        raise ValueError("La fecha de ejercicio contable es obligatoria.")

    fecha_operacion_iso_validada = fecha_operacion_iso.strip()

    if not _PATRON_FECHA_ISO_EJERCICIO_CONTABLE.match(fecha_operacion_iso_validada):
        raise ValueError("La fecha de ejercicio contable debe tener formato YYYY-MM-DD.")

    try:
        datetime.strptime(fecha_operacion_iso_validada, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            "La fecha de ejercicio contable debe ser una fecha valida."
        ) from exc

    return fecha_operacion_iso_validada
