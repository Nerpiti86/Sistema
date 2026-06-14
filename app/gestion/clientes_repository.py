import sqlite3
from datetime import datetime
from typing import Any

from app.db import get_db

_COLUMNAS_SELECT_CLIENTES = """
    clientes.id,
    clientes.razon_social,
    clientes.nombre_fantasia,
    clientes.grupo_cliente_id,
    clientes.telefono,
    clientes.email,
    clientes.domicilio,
    clientes.codigo_postal,
    clientes.ciudad,
    clientes.pais_id,
    clientes.provincia_id,
    clientes.condicion_iva_codigo,
    clientes.tipo_documento_fiscal_codigo,
    clientes.numero_documento_fiscal,
    clientes.cuenta_deudores_ventas_codigo,
    clientes.cuenta_anticipo_clientes_codigo,
    clientes.activo,
    clientes.orden,
    clientes.observaciones,
    clientes.creado_en,
    clientes.actualizado_en,
    grupos_clientes.nombre AS grupo_cliente_nombre,
    paises.nombre AS pais_nombre,
    paises.codigo_iso AS pais_codigo_iso,
    provincias.nombre AS provincia_nombre,
    condiciones_iva.descripcion AS condicion_iva_descripcion,
    tipos_documento.descripcion AS tipo_documento_fiscal_descripcion,
    cuenta_deudores.descripcion AS cuenta_deudores_ventas_descripcion,
    cuenta_anticipos.descripcion AS cuenta_anticipo_clientes_descripcion
"""


def listar_clientes() -> list[dict[str, Any]]:
    """
    Devuelve clientes ordenados para gestion.

    El maestro se mantiene sin paginar en esta etapa inicial. Si el volumen
    crece, el repository debera incorporar filtros y paginacion SQL.
    """
    filas_clientes = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CLIENTES}
        FROM clientes
        JOIN grupos_clientes
          ON grupos_clientes.id = clientes.grupo_cliente_id
        LEFT JOIN paises
          ON paises.id = clientes.pais_id
        LEFT JOIN provincias
          ON provincias.id = clientes.provincia_id
        LEFT JOIN condiciones_iva
          ON condiciones_iva.codigo = clientes.condicion_iva_codigo
        LEFT JOIN tipos_documento
          ON tipos_documento.codigo = clientes.tipo_documento_fiscal_codigo
        LEFT JOIN cuentas_contables AS cuenta_deudores
          ON cuenta_deudores.cuenta = clientes.cuenta_deudores_ventas_codigo
        LEFT JOIN cuentas_contables AS cuenta_anticipos
          ON cuenta_anticipos.cuenta = clientes.cuenta_anticipo_clientes_codigo
        ORDER BY clientes.activo DESC, clientes.orden, clientes.razon_social
        """
    ).fetchall()

    return [_normalizar_fila_cliente(fila_cliente) for fila_cliente in filas_clientes]


def listar_clientes_activos() -> list[dict[str, Any]]:
    """Devuelve clientes activos ordenados para selects y operaciones."""
    filas_clientes = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CLIENTES}
        FROM clientes
        JOIN grupos_clientes
          ON grupos_clientes.id = clientes.grupo_cliente_id
        LEFT JOIN paises
          ON paises.id = clientes.pais_id
        LEFT JOIN provincias
          ON provincias.id = clientes.provincia_id
        LEFT JOIN condiciones_iva
          ON condiciones_iva.codigo = clientes.condicion_iva_codigo
        LEFT JOIN tipos_documento
          ON tipos_documento.codigo = clientes.tipo_documento_fiscal_codigo
        LEFT JOIN cuentas_contables AS cuenta_deudores
          ON cuenta_deudores.cuenta = clientes.cuenta_deudores_ventas_codigo
        LEFT JOIN cuentas_contables AS cuenta_anticipos
          ON cuenta_anticipos.cuenta = clientes.cuenta_anticipo_clientes_codigo
        WHERE clientes.activo = 1
        ORDER BY clientes.orden, clientes.razon_social
        """
    ).fetchall()

    return [_normalizar_fila_cliente(fila_cliente) for fila_cliente in filas_clientes]


def obtener_cliente_por_id(cliente_id: Any) -> dict[str, Any] | None:
    """Devuelve un cliente por id, o None si no existe."""
    cliente_id_validado = _validar_id_cliente(cliente_id)

    fila_cliente = get_db().execute(
        f"""
        SELECT {_COLUMNAS_SELECT_CLIENTES}
        FROM clientes
        JOIN grupos_clientes
          ON grupos_clientes.id = clientes.grupo_cliente_id
        LEFT JOIN paises
          ON paises.id = clientes.pais_id
        LEFT JOIN provincias
          ON provincias.id = clientes.provincia_id
        LEFT JOIN condiciones_iva
          ON condiciones_iva.codigo = clientes.condicion_iva_codigo
        LEFT JOIN tipos_documento
          ON tipos_documento.codigo = clientes.tipo_documento_fiscal_codigo
        LEFT JOIN cuentas_contables AS cuenta_deudores
          ON cuenta_deudores.cuenta = clientes.cuenta_deudores_ventas_codigo
        LEFT JOIN cuentas_contables AS cuenta_anticipos
          ON cuenta_anticipos.cuenta = clientes.cuenta_anticipo_clientes_codigo
        WHERE clientes.id = ?
        LIMIT 1
        """,
        (cliente_id_validado,),
    ).fetchone()

    if fila_cliente is None:
        return None

    return _normalizar_fila_cliente(fila_cliente)


def crear_cliente(datos_cliente: dict[str, Any]) -> dict[str, Any]:
    """Inserta un cliente y devuelve la fila creada."""
    datos_validados = _validar_datos_cliente(datos_cliente)
    creado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                INSERT INTO clientes (
                    razon_social,
                    nombre_fantasia,
                    grupo_cliente_id,
                    telefono,
                    email,
                    domicilio,
                    codigo_postal,
                    ciudad,
                    pais_id,
                    provincia_id,
                    condicion_iva_codigo,
                    tipo_documento_fiscal_codigo,
                    numero_documento_fiscal,
                    cuenta_deudores_ventas_codigo,
                    cuenta_anticipo_clientes_codigo,
                    activo,
                    orden,
                    observaciones,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos_validados["razon_social"],
                    datos_validados["nombre_fantasia"],
                    datos_validados["grupo_cliente_id"],
                    datos_validados["telefono"],
                    datos_validados["email"],
                    datos_validados["domicilio"],
                    datos_validados["codigo_postal"],
                    datos_validados["ciudad"],
                    datos_validados["pais_id"],
                    datos_validados["provincia_id"],
                    datos_validados["condicion_iva_codigo"],
                    datos_validados["tipo_documento_fiscal_codigo"],
                    datos_validados["numero_documento_fiscal"],
                    datos_validados["cuenta_deudores_ventas_codigo"],
                    datos_validados["cuenta_anticipo_clientes_codigo"],
                    datos_validados["activo"],
                    datos_validados["orden"],
                    datos_validados["observaciones"],
                    creado_en,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo crear el cliente. Revise grupo, datos fiscales, "
            "geografia, cuentas contables o documento duplicado."
        ) from exc

    cliente = obtener_cliente_por_id(cursor.lastrowid)

    if cliente is None:
        raise ValueError("No se pudo recuperar el cliente creado.")

    return cliente


def actualizar_cliente_por_id(
    cliente_id: Any,
    datos_cliente: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza campos mutables de un cliente y devuelve la fila final."""
    cliente_id_validado = _validar_id_cliente(cliente_id)

    if obtener_cliente_por_id(cliente_id_validado) is None:
        raise ValueError("No existe el cliente informado.")

    datos_validados = _validar_datos_cliente(datos_cliente)
    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    db = get_db()

    try:
        with db:
            cursor = db.execute(
                """
                UPDATE clientes
                SET
                    razon_social = ?,
                    nombre_fantasia = ?,
                    grupo_cliente_id = ?,
                    telefono = ?,
                    email = ?,
                    domicilio = ?,
                    codigo_postal = ?,
                    ciudad = ?,
                    pais_id = ?,
                    provincia_id = ?,
                    condicion_iva_codigo = ?,
                    tipo_documento_fiscal_codigo = ?,
                    numero_documento_fiscal = ?,
                    cuenta_deudores_ventas_codigo = ?,
                    cuenta_anticipo_clientes_codigo = ?,
                    activo = ?,
                    orden = ?,
                    observaciones = ?,
                    actualizado_en = ?
                WHERE id = ?
                """,
                (
                    datos_validados["razon_social"],
                    datos_validados["nombre_fantasia"],
                    datos_validados["grupo_cliente_id"],
                    datos_validados["telefono"],
                    datos_validados["email"],
                    datos_validados["domicilio"],
                    datos_validados["codigo_postal"],
                    datos_validados["ciudad"],
                    datos_validados["pais_id"],
                    datos_validados["provincia_id"],
                    datos_validados["condicion_iva_codigo"],
                    datos_validados["tipo_documento_fiscal_codigo"],
                    datos_validados["numero_documento_fiscal"],
                    datos_validados["cuenta_deudores_ventas_codigo"],
                    datos_validados["cuenta_anticipo_clientes_codigo"],
                    datos_validados["activo"],
                    datos_validados["orden"],
                    datos_validados["observaciones"],
                    actualizado_en,
                    cliente_id_validado,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "No se pudo actualizar el cliente. Revise grupo, datos fiscales, "
            "geografia, cuentas contables o documento duplicado."
        ) from exc

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el cliente.")

    cliente = obtener_cliente_por_id(cliente_id_validado)

    if cliente is None:
        raise ValueError("No se pudo recuperar el cliente actualizado.")

    return cliente


def cambiar_estado_cliente(cliente_id: Any, activo: Any) -> dict[str, Any]:
    """Activa o desactiva un cliente sin borrado fisico."""
    cliente_id_validado = _validar_id_cliente(cliente_id)
    activo_validado = _validar_activo(activo)

    if obtener_cliente_por_id(cliente_id_validado) is None:
        raise ValueError("No existe el cliente informado.")

    actualizado_en = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()

    with db:
        cursor = db.execute(
            """
            UPDATE clientes
            SET activo = ?, actualizado_en = ?
            WHERE id = ?
            """,
            (activo_validado, actualizado_en, cliente_id_validado),
        )

    if cursor.rowcount != 1:
        raise ValueError("No se pudo actualizar el estado del cliente.")

    cliente = obtener_cliente_por_id(cliente_id_validado)

    if cliente is None:
        raise ValueError("No se pudo recuperar el cliente actualizado.")

    return cliente


def validar_cliente_activo(cliente_id: Any) -> bool:
    """Valida que un cliente exista y este activo."""
    cliente_id_validado = _validar_id_cliente(cliente_id)

    fila_cliente = get_db().execute(
        """
        SELECT 1
        FROM clientes
        WHERE id = ?
          AND activo = 1
        LIMIT 1
        """,
        (cliente_id_validado,),
    ).fetchone()

    if fila_cliente is None:
        raise ValueError("El cliente no existe o no esta activo.")

    return True


def _normalizar_fila_cliente(fila_cliente) -> dict[str, Any]:
    """Convierte una fila SQLite de clientes en dict explicito."""
    cliente = dict(fila_cliente)

    cliente["id"] = int(cliente["id"])
    cliente["grupo_cliente_id"] = int(cliente["grupo_cliente_id"])
    cliente["activo"] = int(cliente["activo"])
    cliente["orden"] = int(cliente["orden"])
    cliente["esta_activo"] = cliente["activo"] == 1

    for campo in ("pais_id", "provincia_id"):
        if cliente.get(campo) is not None:
            cliente[campo] = int(cliente[campo])

    cliente["nombre_visible"] = cliente.get("nombre_fantasia") or cliente["razon_social"]
    cliente["descripcion_select"] = cliente["nombre_visible"]

    if cliente.get("tipo_documento_fiscal_descripcion") and cliente.get(
        "numero_documento_fiscal"
    ):
        cliente["documento_fiscal_descripcion"] = (
            f"{cliente['tipo_documento_fiscal_descripcion']} "
            f"{cliente['numero_documento_fiscal']}"
        )
    else:
        cliente["documento_fiscal_descripcion"] = None

    if cliente.get("pais_nombre") and cliente.get("pais_codigo_iso"):
        cliente["pais_descripcion"] = (
            f"{cliente['pais_nombre']} ({cliente['pais_codigo_iso']})"
        )
    else:
        cliente["pais_descripcion"] = cliente.get("pais_nombre")

    return cliente


def _validar_datos_cliente(datos_cliente: dict[str, Any]) -> dict[str, Any]:
    razon_social = _validar_texto_obligatorio(
        datos_cliente.get("razon_social"),
        "La razon social del cliente es obligatoria.",
    )
    grupo_cliente_id = _validar_id_obligatorio(
        datos_cliente.get("grupo_cliente_id"),
        "El id del grupo de clientes debe ser numerico.",
        "El id del grupo de clientes debe ser positivo.",
    )
    pais_id = _validar_id_opcional(
        datos_cliente.get("pais_id"),
        "El id del pais debe ser numerico.",
        "El id del pais debe ser positivo.",
    )
    provincia_id = _validar_id_opcional(
        datos_cliente.get("provincia_id"),
        "El id de la provincia debe ser numerico.",
        "El id de la provincia debe ser positivo.",
    )

    if provincia_id is not None and pais_id is None:
        raise ValueError("Para informar provincia tambien debe informarse pais.")

    tipo_documento_fiscal_codigo = _validar_texto_opcional(
        datos_cliente.get("tipo_documento_fiscal_codigo")
    )
    numero_documento_fiscal = _validar_texto_opcional(
        datos_cliente.get("numero_documento_fiscal")
    )

    if bool(tipo_documento_fiscal_codigo) != bool(numero_documento_fiscal):
        raise ValueError("El tipo y numero de documento fiscal deben informarse juntos.")

    return {
        "razon_social": razon_social,
        "nombre_fantasia": _validar_texto_opcional(
            datos_cliente.get("nombre_fantasia")
        ),
        "grupo_cliente_id": grupo_cliente_id,
        "telefono": _validar_texto_opcional(datos_cliente.get("telefono")),
        "email": _validar_texto_opcional(datos_cliente.get("email")),
        "domicilio": _validar_texto_opcional(datos_cliente.get("domicilio")),
        "codigo_postal": _validar_texto_opcional(datos_cliente.get("codigo_postal")),
        "ciudad": _validar_texto_opcional(datos_cliente.get("ciudad")),
        "pais_id": pais_id,
        "provincia_id": provincia_id,
        "condicion_iva_codigo": _validar_texto_opcional(
            datos_cliente.get("condicion_iva_codigo")
        ),
        "tipo_documento_fiscal_codigo": tipo_documento_fiscal_codigo,
        "numero_documento_fiscal": numero_documento_fiscal,
        "cuenta_deudores_ventas_codigo": _validar_texto_opcional(
            datos_cliente.get("cuenta_deudores_ventas_codigo")
        ),
        "cuenta_anticipo_clientes_codigo": _validar_texto_opcional(
            datos_cliente.get("cuenta_anticipo_clientes_codigo")
        ),
        "activo": _validar_activo(datos_cliente.get("activo", 1)),
        "orden": _validar_orden(datos_cliente.get("orden", 0)),
        "observaciones": _validar_texto_opcional(datos_cliente.get("observaciones")),
    }


def _validar_id_cliente(cliente_id: Any) -> int:
    try:
        cliente_id_validado = int(str(cliente_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del cliente debe ser numerico.") from exc

    if cliente_id_validado <= 0:
        raise ValueError("El id del cliente debe ser positivo.")

    return cliente_id_validado


def _validar_id_obligatorio(
    valor: Any,
    mensaje_tipo: str,
    mensaje_positivo: str,
) -> int:
    try:
        valor_validado = int(str(valor or "").strip())
    except ValueError as exc:
        raise ValueError(mensaje_tipo) from exc

    if valor_validado <= 0:
        raise ValueError(mensaje_positivo)

    return valor_validado


def _validar_id_opcional(
    valor: Any,
    mensaje_tipo: str,
    mensaje_positivo: str,
) -> int | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    try:
        valor_validado = int(valor_normalizado)
    except ValueError as exc:
        raise ValueError(mensaje_tipo) from exc

    if valor_validado <= 0:
        raise ValueError(mensaje_positivo)

    return valor_validado


def _validar_texto_obligatorio(valor: Any, mensaje_error: str) -> str:
    valor_validado = str(valor or "").strip()

    if not valor_validado:
        raise ValueError(mensaje_error)

    return valor_validado


def _validar_texto_opcional(valor: Any) -> str | None:
    valor_validado = str(valor or "").strip()

    if not valor_validado:
        return None

    return valor_validado


def _validar_activo(activo: Any) -> int:
    if isinstance(activo, bool):
        return 1 if activo else 0

    if isinstance(activo, int) and activo in (0, 1):
        return activo

    activo_normalizado = str(activo or "").strip()

    if activo_normalizado in {"0", "1"}:
        return int(activo_normalizado)

    raise ValueError("El estado activo del cliente es invalido.")


def _validar_orden(orden: Any) -> int:
    try:
        orden_validado = int(str(orden or "0").strip())
    except ValueError as exc:
        raise ValueError("El orden del cliente debe ser numerico.") from exc

    if orden_validado < 0:
        raise ValueError("El orden del cliente no puede ser negativo.")

    return orden_validado
