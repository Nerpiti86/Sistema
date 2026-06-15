from typing import Any

from app.contabilidad.cuentas_contables_repository import (
    listar_cuentas_contables,
    validar_cuenta_contable_imputable,
)
from app.gestion.articulos_venta_repository import (
    actualizar_articulo_venta_por_id,
    cambiar_estado_articulo_venta,
    crear_articulo_venta,
    listar_articulos_venta,
    obtener_articulo_venta_por_id,
)
from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    normalizar_decimal_argentino_a_entero_escala,
)
from app.shared.monedas_repository import listar_monedas_activas, validar_moneda_activa

_TIPOS_ARTICULO_VENTA = ("PRODUCTO", "SERVICIO")
_ESCALA_IMPORTE_CENTAVOS = 2
_ESCALA_COTIZACION = 6
_FACTOR_COTIZACION = 10**_ESCALA_COTIZACION
_MONEDA_CONTABLE = "ARS"


def obtener_contexto_listado_articulos_venta() -> dict[str, Any]:
    """
    Devuelve contexto chico del maestro productos o servicios.

    Este service no ejecuta SQL directo. La lectura queda delegada al repository
    funcional de gestion.
    """
    articulos_venta = [
        _preparar_articulo_venta_para_pantalla(articulo)
        for articulo in listar_articulos_venta()
    ]
    articulos_venta_activos = [
        articulo for articulo in articulos_venta if articulo["esta_activo"]
    ]

    return {
        "articulos_venta": articulos_venta,
        "articulos_venta_activos": articulos_venta_activos,
        "cantidad_articulos_venta": len(articulos_venta),
        "cantidad_articulos_venta_activos": len(articulos_venta_activos),
    }


def obtener_contexto_formulario_articulo_venta(
    articulo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Devuelve contexto para formularios de productos o servicios."""
    articulo_form = _preparar_articulo_venta_para_formulario(articulo or {})
    articulo_form.setdefault("activo", 1)
    articulo_form.setdefault("orden", 0)

    monedas = listar_monedas_activas()
    cuentas_contables_imputables = [
        cuenta
        for cuenta in listar_cuentas_contables()
        if cuenta["es_imputable"]
    ]

    return {
        "articulo": articulo_form,
        "tipos_articulo_venta": list(_TIPOS_ARTICULO_VENTA),
        "monedas": monedas,
        "cuentas_contables_imputables": cuentas_contables_imputables,
        "cantidad_tipos_articulo_venta": len(_TIPOS_ARTICULO_VENTA),
        "cantidad_monedas": len(monedas),
        "cantidad_cuentas_contables_imputables": len(cuentas_contables_imputables),
    }


def obtener_contexto_edicion_articulo_venta(articulo_venta_id: Any) -> dict[str, Any]:
    """Devuelve contexto para editar un producto o servicio existente."""
    articulo_venta_id_normalizado = normalizar_id_articulo_venta_desde_formulario(
        articulo_venta_id
    )
    articulo = obtener_articulo_venta_por_id(articulo_venta_id_normalizado)

    if articulo is None:
        raise ValueError("No existe el producto o servicio informado.")

    return obtener_contexto_formulario_articulo_venta(articulo)


def crear_articulo_venta_desde_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Crea un producto o servicio desde datos de formulario."""
    datos_articulo = _normalizar_datos_articulo_venta_formulario(formulario)
    _validar_referencias_operativas_articulo_venta(datos_articulo)

    return crear_articulo_venta(datos_articulo)


def actualizar_articulo_venta_desde_formulario(
    articulo_venta_id: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza un producto o servicio desde datos de formulario."""
    datos_articulo = _normalizar_datos_articulo_venta_formulario(formulario)
    _validar_referencias_operativas_articulo_venta(datos_articulo)

    return actualizar_articulo_venta_por_id(articulo_venta_id, datos_articulo)


def activar_articulo_venta(articulo_venta_id: Any) -> dict[str, Any]:
    """Activa un producto o servicio sin borrado fisico."""
    return cambiar_estado_articulo_venta(articulo_venta_id, 1)


def desactivar_articulo_venta(articulo_venta_id: Any) -> dict[str, Any]:
    """Desactiva un producto o servicio sin borrado fisico."""
    return cambiar_estado_articulo_venta(articulo_venta_id, 0)


def normalizar_id_articulo_venta_desde_formulario(articulo_venta_id: Any) -> int:
    """Normaliza id de producto o servicio recibido desde formularios."""
    try:
        articulo_venta_id_normalizado = int(str(articulo_venta_id).strip())
    except ValueError as exc:
        raise ValueError("El id del producto o servicio debe ser numerico.") from exc

    if articulo_venta_id_normalizado <= 0:
        raise ValueError("El id del producto o servicio debe ser positivo.")

    return articulo_venta_id_normalizado


def _preparar_articulo_venta_para_pantalla(
    articulo: dict[str, Any],
) -> dict[str, Any]:
    """Agrega representaciones visuales sin modificar el contrato persistido."""
    articulo_pantalla = dict(articulo)
    articulo_pantalla["precio_unitario_sugerido_argentina"] = (
        _formatear_precio_sugerido_centavos_a_importe_argentino(
            articulo_pantalla.get("precio_unitario_sugerido_centavos", 0)
        )
    )
    articulo_pantalla["cotizacion_argentina"] = _formatear_cotizacion_articulo(
        articulo_pantalla.get("cotizacion_1000000", 1000000)
    )
    articulo_pantalla["precio_unitario_sugerido_ars_centavos"] = (
        _calcular_precio_sugerido_ars_centavos(
            articulo_pantalla.get("precio_unitario_sugerido_centavos", 0),
            articulo_pantalla.get("cotizacion_1000000", 1000000),
        )
    )
    articulo_pantalla["precio_unitario_sugerido_ars_argentina"] = (
        _formatear_precio_sugerido_centavos_a_importe_argentino(
            articulo_pantalla["precio_unitario_sugerido_ars_centavos"]
        )
    )

    return articulo_pantalla


def _preparar_articulo_venta_para_formulario(
    articulo: dict[str, Any],
) -> dict[str, Any]:
    """Prepara valores visibles del formulario preservando entradas invalidas."""
    articulo_form = dict(articulo)
    articulo_form.setdefault("precio_unitario_sugerido_centavos", 0)
    articulo_form["precio_unitario_sugerido_argentina"] = (
        _formatear_precio_sugerido_para_formulario(
            articulo_form.get("precio_unitario_sugerido_centavos")
        )
    )
    articulo_form.setdefault("cotizacion_1000000", 1000000)
    articulo_form["cotizacion_argentina"] = _formatear_cotizacion_para_formulario(
        articulo_form.get("cotizacion_1000000")
    )
    articulo_form["precio_unitario_sugerido_ars_argentina"] = (
        _formatear_precio_sugerido_ars_para_formulario(
            articulo_form.get("precio_unitario_sugerido_centavos"),
            articulo_form.get("cotizacion_1000000"),
        )
    )

    return articulo_form


def _formatear_precio_sugerido_para_formulario(valor: Any) -> str:
    if isinstance(valor, str):
        valor_texto = valor.strip()

        if not valor_texto:
            return "0,00"

        return valor_texto

    valor_texto = str(valor or "").strip()

    if not valor_texto:
        return "0,00"

    try:
        valor_entero = int(valor_texto)
    except ValueError:
        return valor_texto

    return _formatear_precio_sugerido_centavos_a_importe_argentino(valor_entero)


def _formatear_precio_sugerido_centavos_a_importe_argentino(valor: Any) -> str:
    try:
        valor_entero = int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError("El precio sugerido guardado es invalido.") from exc

    if valor_entero < 0:
        raise ValueError("El precio sugerido guardado es invalido.")

    return formatear_entero_escala_a_decimal_argentino(
        valor_entero,
        _ESCALA_IMPORTE_CENTAVOS,
    )


def _formatear_precio_sugerido_ars_para_formulario(
    precio_centavos: Any,
    cotizacion_1000000: Any,
) -> str:
    try:
        precio_ars_centavos = _calcular_precio_sugerido_ars_centavos(
            precio_centavos,
            cotizacion_1000000,
        )
    except ValueError:
        return ""

    return _formatear_precio_sugerido_centavos_a_importe_argentino(
        precio_ars_centavos
    )


def _calcular_precio_sugerido_ars_centavos(
    precio_centavos: Any,
    cotizacion_1000000: Any,
) -> int:
    try:
        precio_validado = int(precio_centavos)
        cotizacion_validada = int(cotizacion_1000000)
    except (TypeError, ValueError) as exc:
        raise ValueError("No se pudo calcular el precio sugerido ARS.") from exc

    if precio_validado < 0 or cotizacion_validada <= 0:
        raise ValueError("No se pudo calcular el precio sugerido ARS.")

    return (
        precio_validado * cotizacion_validada + (_FACTOR_COTIZACION // 2)
    ) // _FACTOR_COTIZACION


def _formatear_cotizacion_para_formulario(valor: Any) -> str:
    if isinstance(valor, str):
        valor_texto = valor.strip()

        if not valor_texto:
            return ""

        return valor_texto

    return _formatear_cotizacion_articulo(valor or 1000000)


def _formatear_cotizacion_articulo(valor: Any) -> str:
    try:
        valor_entero = int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError("La cotizacion guardada es invalida.") from exc

    if valor_entero <= 0:
        raise ValueError("La cotizacion guardada es invalida.")

    return formatear_entero_escala_a_decimal_argentino(
        valor_entero,
        _ESCALA_COTIZACION,
    )


def _normalizar_datos_articulo_venta_formulario(
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de productos o servicios."""
    moneda_codigo = _obtener_valor_formulario(formulario, "moneda_codigo").upper()

    return {
        "nombre": _obtener_valor_formulario(formulario, "nombre"),
        "tipo": _obtener_valor_formulario(formulario, "tipo"),
        "moneda_codigo": moneda_codigo,
        "precio_unitario_sugerido_centavos": (
            _normalizar_precio_sugerido_formulario_a_centavos(
                _obtener_valor_formulario(
                    formulario,
                    "precio_unitario_sugerido_centavos",
                )
            )
        ),
        "cotizacion_1000000": _normalizar_cotizacion_articulo_formulario(
            moneda_codigo,
            _obtener_valor_formulario(formulario, "cotizacion_1000000"),
        ),
        "cuenta_ingreso_codigo": _obtener_valor_formulario(
            formulario,
            "cuenta_ingreso_codigo",
        ),
        "activo": _obtener_valor_checkbox_0_1(formulario, "activo"),
        "orden": _obtener_valor_formulario(formulario, "orden"),
        "observaciones": _obtener_valor_formulario(formulario, "observaciones"),
    }


def _normalizar_precio_sugerido_formulario_a_centavos(valor: Any) -> int:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return 0

    try:
        centavos = normalizar_decimal_argentino_a_entero_escala(
            valor_normalizado,
            _ESCALA_IMPORTE_CENTAVOS,
        )
    except ValueError as exc:
        raise ValueError(
            "El precio sugerido debe respetar formato argentino 9.999,99."
        ) from exc

    if centavos < 0:
        raise ValueError("El precio sugerido no puede ser negativo.")

    return centavos


def _normalizar_cotizacion_articulo_formulario(moneda_codigo: str, valor: Any) -> int:
    if moneda_codigo == _MONEDA_CONTABLE:
        return 1000000

    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        raise ValueError(
            "La cotizacion es obligatoria cuando la moneda no es ARS."
        )

    try:
        cotizacion_1000000 = normalizar_decimal_argentino_a_entero_escala(
            valor_normalizado,
            _ESCALA_COTIZACION,
        )
    except ValueError as exc:
        raise ValueError(
            "La cotizacion debe respetar formato argentino 9.999,999999."
        ) from exc

    if cotizacion_1000000 <= 0:
        raise ValueError("La cotizacion debe ser mayor a cero.")

    return cotizacion_1000000


def _validar_referencias_operativas_articulo_venta(
    datos_articulo: dict[str, Any],
) -> None:
    """Valida referencias activas antes de delegar persistencia al repository."""
    moneda_codigo = _normalizar_texto_opcional(datos_articulo.get("moneda_codigo"))

    if moneda_codigo is None:
        raise ValueError("La moneda del producto o servicio es obligatoria.")

    validar_moneda_activa(moneda_codigo)

    cuenta_ingreso_codigo = _normalizar_texto_opcional(
        datos_articulo.get("cuenta_ingreso_codigo")
    )

    if cuenta_ingreso_codigo is not None:
        validar_cuenta_contable_imputable(cuenta_ingreso_codigo)


def _normalizar_texto_opcional(valor: Any) -> str | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    return valor_normalizado


def _obtener_valor_formulario(formulario: dict[str, Any], campo: str) -> str:
    """Lee valor de formulario y devuelve texto recortado."""
    return str(formulario.get(campo, "") or "").strip()


def _obtener_valor_checkbox_0_1(formulario: dict[str, Any], campo: str) -> int:
    """Normaliza checkbox HTML al contrato SQLite 0/1."""
    valor = formulario.get(campo)

    if valor is None:
        return 0

    valor_normalizado = str(valor or "").strip().upper()

    if valor_normalizado in {"", "0", "NO", "FALSE", "OFF"}:
        return 0

    return 1
