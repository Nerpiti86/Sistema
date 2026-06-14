import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db
from app.shared.formatos import normalizar_decimal_argentino_a_entero_escala

TIPOS_MEDIO_OPERATIVO = {
    "BANCO_PROPIO",
    "EFECTIVO",
    "TARJETA",
    "VALORES_CARTERA",
}

_COLUMNAS_SELECT_MEDIOS_OPERATIVOS = """
    mo.id,
    mo.codigo,
    mo.nombre,
    mo.tipo,
    mo.requiere_cotizacion,
    mo.cotizacion_default_centavos,
    mo.banco_codigo,
    mo.plaza,
    mo.sucursal,
    mo.numero_cuenta,
    mo.cuenta_contable_codigo,
    mo.moneda_codigo,
    mo.cuit,
    mo.activo,
    mo.orden,
    mo.creado_en,
    mo.actualizado_en,
    m.nombre AS moneda_nombre,
    m.simbolo AS moneda_simbolo,
    b.nombre AS banco_nombre,
    c.descripcion AS cuenta_contable_descripcion
"""


def listar_medios_operativos() -> list[dict[str, Any]]:
    """Devuelve medios operativos ordenados para uso transversal."""
    filas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MEDIOS_OPERATIVOS}
        FROM medios_operativos mo
        JOIN monedas m ON m.codigo = mo.moneda_codigo
        JOIN cuentas_contables c ON c.cuenta = mo.cuenta_contable_codigo
        LEFT JOIN bancos b ON b.codigo = mo.banco_codigo
        ORDER BY mo.orden, mo.codigo
        """
    ).fetchall()

    return [_normalizar_fila_medio_operativo(fila) for fila in filas]


def listar_medios_operativos_activos() -> list[dict[str, Any]]:
    """Devuelve medios operativos activos ordenados para formularios."""
    filas = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MEDIOS_OPERATIVOS}
        FROM medios_operativos mo
        JOIN monedas m ON m.codigo = mo.moneda_codigo
        JOIN cuentas_contables c ON c.cuenta = mo.cuenta_contable_codigo
        LEFT JOIN bancos b ON b.codigo = mo.banco_codigo
        WHERE mo.activo = 1
        ORDER BY mo.orden, mo.codigo
        """
    ).fetchall()

    return [_normalizar_fila_medio_operativo(fila) for fila in filas]


def obtener_medio_operativo_por_codigo(codigo: Any) -> dict[str, Any] | None:
    """Devuelve un medio operativo por codigo visible, o None si no existe."""
    codigo_validado = _validar_codigo(codigo)
    fila = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_MEDIOS_OPERATIVOS}
        FROM medios_operativos mo
        JOIN monedas m ON m.codigo = mo.moneda_codigo
        JOIN cuentas_contables c ON c.cuenta = mo.cuenta_contable_codigo
        LEFT JOIN bancos b ON b.codigo = mo.banco_codigo
        WHERE mo.codigo = ?
        LIMIT 1
        """,
        (codigo_validado,),
    ).fetchone()

    if fila is None:
        return None

    return _normalizar_fila_medio_operativo(fila)


def crear_medio_operativo(datos: dict[str, Any]) -> dict[str, Any]:
    """Inserta un medio operativo y devuelve la fila creada."""
    datos_validados = _validar_datos_medio_operativo(datos)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    try:
        with db:
            db.execute(
                """
                INSERT INTO medios_operativos (
                    codigo,
                    nombre,
                    tipo,
                    requiere_cotizacion,
                    cotizacion_default_centavos,
                    banco_codigo,
                    plaza,
                    sucursal,
                    numero_cuenta,
                    cuenta_contable_codigo,
                    moneda_codigo,
                    cuit,
                    activo,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos_validados["codigo"],
                    datos_validados["nombre"],
                    datos_validados["tipo"],
                    datos_validados["requiere_cotizacion"],
                    datos_validados["cotizacion_default_centavos"],
                    datos_validados["banco_codigo"],
                    datos_validados["plaza"],
                    datos_validados["sucursal"],
                    datos_validados["numero_cuenta"],
                    datos_validados["cuenta_contable_codigo"],
                    datos_validados["moneda_codigo"],
                    datos_validados["cuit"],
                    datos_validados["activo"],
                    datos_validados["orden"],
                    creado_en,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("No se pudo crear el medio operativo.") from exc

    medio_operativo = obtener_medio_operativo_por_codigo(datos_validados["codigo"])

    if medio_operativo is None:
        raise ValueError("No se pudo recuperar el medio operativo creado.")

    return medio_operativo


def actualizar_medio_operativo_por_codigo(
    codigo: Any,
    datos: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de un medio operativo."""
    codigo_validado = _validar_codigo(codigo)

    if obtener_medio_operativo_por_codigo(codigo_validado) is None:
        raise ValueError("No existe el medio operativo informado.")

    datos_validados = _validar_datos_medio_operativo(
        {
            **datos,
            "codigo": codigo_validado,
        }
    )
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE medios_operativos
            SET
                nombre = ?,
                tipo = ?,
                requiere_cotizacion = ?,
                cotizacion_default_centavos = ?,
                banco_codigo = ?,
                plaza = ?,
                sucursal = ?,
                numero_cuenta = ?,
                cuenta_contable_codigo = ?,
                moneda_codigo = ?,
                cuit = ?,
                activo = ?,
                orden = ?,
                actualizado_en = ?
            WHERE codigo = ?
            """,
            (
                datos_validados["nombre"],
                datos_validados["tipo"],
                datos_validados["requiere_cotizacion"],
                datos_validados["cotizacion_default_centavos"],
                datos_validados["banco_codigo"],
                datos_validados["plaza"],
                datos_validados["sucursal"],
                datos_validados["numero_cuenta"],
                datos_validados["cuenta_contable_codigo"],
                datos_validados["moneda_codigo"],
                datos_validados["cuit"],
                datos_validados["activo"],
                datos_validados["orden"],
                actualizado_en,
                codigo_validado,
            ),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el medio operativo.")

    medio_operativo = obtener_medio_operativo_por_codigo(codigo_validado)

    if medio_operativo is None:
        raise ValueError("No se pudo recuperar el medio operativo actualizado.")

    return medio_operativo


def cambiar_estado_medio_operativo(codigo: Any, activo: Any) -> dict[str, Any]:
    """Activa o desactiva un medio operativo sin borrado fisico."""
    codigo_validado = _validar_codigo(codigo)
    activo_validado = _validar_activo(activo)

    if obtener_medio_operativo_por_codigo(codigo_validado) is None:
        raise ValueError("No existe el medio operativo informado.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE medios_operativos
            SET activo = ?, actualizado_en = ?
            WHERE codigo = ?
            """,
            (activo_validado, actualizado_en, codigo_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el estado del medio operativo.")

    medio_operativo = obtener_medio_operativo_por_codigo(codigo_validado)

    if medio_operativo is None:
        raise ValueError("No se pudo recuperar el medio operativo actualizado.")

    return medio_operativo


def validar_medio_operativo_activo(codigo: Any) -> bool:
    """Valida que un medio operativo exista y este activo."""
    codigo_validado = _validar_codigo(codigo)
    fila = get_db().execute(
        """
        SELECT 1
        FROM medios_operativos
        WHERE codigo = ? AND activo = 1
        LIMIT 1
        """,
        (codigo_validado,),
    ).fetchone()

    if fila is None:
        raise ValueError("El medio operativo no existe o no esta activo.")

    return True


def _normalizar_fila_medio_operativo(fila) -> dict[str, Any]:
    medio = dict(fila)
    medio["requiere_cotizacion"] = int(medio["requiere_cotizacion"])
    medio["activo"] = int(medio["activo"])
    medio["orden"] = int(medio["orden"])
    medio["esta_activo"] = medio["activo"] == 1
    medio["usa_cotizacion"] = medio["requiere_cotizacion"] == 1
    medio["descripcion_select"] = f"{medio['codigo']} - {medio['nombre']}"
    return medio


def _validar_datos_medio_operativo(datos: dict[str, Any]) -> dict[str, Any]:
    tipo = _validar_tipo(datos["tipo"])
    moneda_codigo = _validar_moneda_codigo(datos["moneda_codigo"])
    banco_codigo = _normalizar_nullable(datos.get("banco_codigo"))
    plaza = _normalizar_nullable(datos.get("plaza"))
    sucursal = _normalizar_nullable(datos.get("sucursal"))
    numero_cuenta = _normalizar_nullable(datos.get("numero_cuenta"))
    cuit = _normalizar_nullable(datos.get("cuit"))
    requiere_cotizacion = _validar_activo(datos.get("requiere_cotizacion", 0))
    cotizacion_default_centavos = _validar_centavos_nullable(
        datos.get("cotizacion_default_centavos")
    )

    if tipo == "BANCO_PROPIO" and banco_codigo is None:
        raise ValueError("El banco es obligatorio para medios de tipo banco propio.")

    if tipo != "BANCO_PROPIO":
        banco_codigo = None
        plaza = None
        sucursal = None
        numero_cuenta = None
        cuit = None

    if moneda_codigo == "ARS":
        requiere_cotizacion = 0
        cotizacion_default_centavos = None

    if requiere_cotizacion == 0:
        cotizacion_default_centavos = None

    return {
        "codigo": _validar_codigo(datos["codigo"]),
        "nombre": _validar_texto_obligatorio(
            datos["nombre"],
            "El nombre del medio operativo es obligatorio.",
        ),
        "tipo": tipo,
        "requiere_cotizacion": requiere_cotizacion,
        "cotizacion_default_centavos": cotizacion_default_centavos,
        "banco_codigo": banco_codigo,
        "plaza": plaza,
        "sucursal": sucursal,
        "numero_cuenta": numero_cuenta,
        "cuenta_contable_codigo": _validar_texto_obligatorio(
            datos["cuenta_contable_codigo"],
            "La cuenta contable del medio operativo es obligatoria.",
        ),
        "moneda_codigo": moneda_codigo,
        "cuit": cuit,
        "activo": _validar_activo(datos.get("activo", 1)),
        "orden": _validar_orden(datos.get("orden", 0)),
    }


def _validar_codigo(codigo: Any) -> str:
    codigo_validado = str(codigo or "").strip().upper()

    if not codigo_validado:
        raise ValueError("El codigo del medio operativo es obligatorio.")

    return codigo_validado


def _validar_tipo(tipo: Any) -> str:
    tipo_validado = str(tipo or "").strip().upper()

    if tipo_validado not in TIPOS_MEDIO_OPERATIVO:
        raise ValueError("El tipo del medio operativo es invalido.")

    return tipo_validado


def _validar_moneda_codigo(moneda_codigo: Any) -> str:
    moneda_codigo_validado = str(moneda_codigo or "").strip().upper()

    if len(moneda_codigo_validado) != 3 or not moneda_codigo_validado.isalpha():
        raise ValueError("La moneda del medio operativo es obligatoria.")

    return moneda_codigo_validado


def _validar_texto_obligatorio(valor: Any, mensaje_error: str) -> str:
    valor_validado = str(valor or "").strip()

    if not valor_validado:
        raise ValueError(mensaje_error)

    return valor_validado


def _normalizar_nullable(valor: Any) -> str | None:
    if valor is None:
        return None

    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return valor_normalizado


def _validar_activo(valor: Any) -> int:
    if isinstance(valor, bool):
        return 1 if valor else 0

    if isinstance(valor, int) and valor in (0, 1):
        return valor

    valor_normalizado = str(valor or "").strip()

    if valor_normalizado in {"0", "1"}:
        return int(valor_normalizado)

    raise ValueError("El valor booleano del medio operativo es invalido.")


def _validar_orden(orden: Any) -> int:
    try:
        orden_validado = int(str(orden or "0").strip())
    except ValueError as exc:
        raise ValueError("El orden del medio operativo debe ser numerico.") from exc

    if orden_validado < 0:
        raise ValueError("El orden del medio operativo no puede ser negativo.")

    return orden_validado


def _validar_centavos_nullable(valor: Any) -> int | None:
    if valor is None:
        return None

    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    try:
        if "," in valor_normalizado:
            centavos = normalizar_decimal_argentino_a_entero_escala(
                valor_normalizado,
                2,
            )
        else:
            centavos = int(valor_normalizado)
    except ValueError as exc:
        raise ValueError("La cotizacion default debe estar expresada en centavos.") from exc

    if centavos < 0:
        raise ValueError("La cotizacion default no puede ser negativa.")

    return centavos
