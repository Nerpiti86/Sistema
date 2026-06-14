from typing import Any

from app.contabilidad.cuentas_contables_repository import (
    listar_cuentas_contables,
    validar_cuenta_contable_imputable,
)
from app.gestion.clientes_repository import (
    actualizar_cliente_por_id,
    cambiar_estado_cliente,
    crear_cliente,
    listar_clientes,
    listar_clientes_activos,
    obtener_cliente_por_id,
    validar_cliente_activo,
)
from app.gestion.grupos_clientes_repository import (
    listar_grupos_clientes_activos,
    validar_grupo_cliente_activo,
)
from app.shared.catalogos_fiscales_repository import (
    listar_catalogo_fiscal_activo,
    validar_item_catalogo_fiscal_activo,
)
from app.shared.paises_repository import listar_paises_activos, validar_pais_activo
from app.shared.provincias_repository import (
    listar_provincias,
    obtener_provincia_por_id,
    validar_provincia_activa,
)


def obtener_contexto_listado_clientes() -> dict[str, Any]:
    """
    Devuelve contexto chico del maestro clientes.

    Este service no ejecuta SQL directo. La lectura queda delegada al repository
    funcional de gestion.
    """
    clientes = listar_clientes()
    clientes_activos = [cliente for cliente in clientes if cliente["esta_activo"]]

    return {
        "clientes": clientes,
        "clientes_activos": clientes_activos,
        "cantidad_clientes": len(clientes),
        "cantidad_clientes_activos": len(clientes_activos),
    }


def obtener_contexto_clientes_activos() -> dict[str, Any]:
    """Devuelve contexto minimo de clientes activos para operaciones."""
    clientes = listar_clientes_activos()

    return {
        "clientes": clientes,
        "cantidad_clientes": len(clientes),
    }


def obtener_contexto_formulario_cliente(
    cliente: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Devuelve contexto para formularios de clientes."""
    cliente_form = dict(cliente or {})
    cliente_form.setdefault("activo", 1)
    cliente_form.setdefault("orden", 0)

    grupos_clientes = listar_grupos_clientes_activos()
    paises = listar_paises_activos()
    provincias = [
        provincia
        for provincia in listar_provincias()
        if provincia["esta_activa"]
    ]
    condiciones_iva = listar_catalogo_fiscal_activo("condiciones_iva")
    tipos_documento = listar_catalogo_fiscal_activo("tipos_documento")
    cuentas_contables_imputables = [
        cuenta
        for cuenta in listar_cuentas_contables()
        if cuenta["es_imputable"]
    ]

    es_alta = not cliente_form.get("id")
    pais_default_id = _obtener_pais_default_id(paises, "Argentina")
    provincia_default_id = _obtener_provincia_default_id(
        provincias,
        "Santa Fe",
        pais_default_id,
    )

    if es_alta and _valor_vacio(cliente_form.get("pais_id")) and pais_default_id is not None:
        cliente_form["pais_id"] = pais_default_id

    if (
        es_alta
        and _valor_vacio(cliente_form.get("provincia_id"))
        and provincia_default_id is not None
    ):
        cliente_form["provincia_id"] = provincia_default_id

    return {
        "cliente": cliente_form,
        "grupos_clientes": grupos_clientes,
        "paises": paises,
        "provincias": provincias,
        "condiciones_iva": condiciones_iva,
        "tipos_documento": tipos_documento,
        "cuentas_contables_imputables": cuentas_contables_imputables,
        "cantidad_grupos_clientes": len(grupos_clientes),
        "cantidad_paises": len(paises),
        "cantidad_provincias": len(provincias),
        "cantidad_condiciones_iva": len(condiciones_iva),
        "cantidad_tipos_documento": len(tipos_documento),
        "cantidad_cuentas_contables_imputables": len(cuentas_contables_imputables),
    }


def obtener_contexto_detalle_cliente(cliente_id: Any) -> dict[str, Any]:
    """Devuelve contexto chico para edicion o consulta de un cliente."""
    cliente_id_normalizado = normalizar_id_cliente_desde_formulario(cliente_id)
    cliente = obtener_cliente_por_id(cliente_id_normalizado)

    if cliente is None:
        raise ValueError("No existe el cliente informado.")

    return {"cliente": cliente}


def obtener_cliente_activo_por_id(cliente_id: Any) -> dict[str, Any]:
    """
    Devuelve un cliente activo por id.

    El service normaliza entrada funcional minima y delega validacion final al
    repository.
    """
    cliente_id_normalizado = normalizar_id_cliente_desde_formulario(cliente_id)
    validar_cliente_activo(cliente_id_normalizado)

    cliente = obtener_cliente_por_id(cliente_id_normalizado)

    if cliente is None:
        raise ValueError("No existe el cliente informado.")

    return cliente


def crear_cliente_desde_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """Crea un cliente desde datos de formulario aplicando reglas funcionales."""
    datos_cliente = _normalizar_datos_cliente_formulario(formulario)
    _validar_referencias_operativas_cliente(datos_cliente)
    return crear_cliente(datos_cliente)


def actualizar_cliente_desde_formulario(
    cliente_id: Any,
    formulario: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza un cliente desde datos de formulario aplicando reglas funcionales."""
    datos_cliente = _normalizar_datos_cliente_formulario(formulario)
    _validar_referencias_operativas_cliente(datos_cliente)
    return actualizar_cliente_por_id(cliente_id, datos_cliente)


def activar_cliente(cliente_id: Any) -> dict[str, Any]:
    """Activa un cliente sin borrado fisico."""
    return cambiar_estado_cliente(cliente_id, 1)


def desactivar_cliente(cliente_id: Any) -> dict[str, Any]:
    """Desactiva un cliente sin borrado fisico."""
    return cambiar_estado_cliente(cliente_id, 0)


def normalizar_id_cliente_desde_formulario(cliente_id: Any) -> int:
    """Normaliza id de cliente recibido desde formularios."""
    try:
        cliente_id_normalizado = int(str(cliente_id or "").strip())
    except ValueError as exc:
        raise ValueError("El id del cliente debe ser numerico.") from exc

    if cliente_id_normalizado <= 0:
        raise ValueError("El id del cliente debe ser positivo.")

    return cliente_id_normalizado


def _obtener_pais_default_id(
    paises: list[dict[str, Any]],
    nombre_default: str,
) -> int | None:
    """Devuelve id de pais default por nombre si existe activo en contexto."""
    nombre_normalizado = _normalizar_texto_comparacion(nombre_default)

    for pais in paises:
        if _normalizar_texto_comparacion(pais.get("nombre")) == nombre_normalizado:
            return int(pais["id"])

    return None


def _obtener_provincia_default_id(
    provincias: list[dict[str, Any]],
    nombre_default: str,
    pais_id: int | None,
) -> int | None:
    """Devuelve id de provincia default por nombre y pais si existe activa."""
    if pais_id is None:
        return None

    nombre_normalizado = _normalizar_texto_comparacion(nombre_default)

    for provincia in provincias:
        if (
            int(provincia["pais_id"]) == int(pais_id)
            and _normalizar_texto_comparacion(provincia.get("nombre")) == nombre_normalizado
        ):
            return int(provincia["id"])

    return None


def _normalizar_texto_comparacion(valor: Any) -> str:
    """Normaliza texto para comparaciones internas de defaults."""
    return str(valor or "").strip().casefold()


def _valor_vacio(valor: Any) -> bool:
    """Indica si un valor de formulario/contexto esta vacio."""
    return str(valor or "").strip() == ""


def _normalizar_datos_cliente_formulario(formulario: dict[str, Any]) -> dict[str, Any]:
    """Normaliza campos recibidos desde formularios de clientes."""
    return {
        "razon_social": _obtener_valor_formulario(formulario, "razon_social"),
        "nombre_fantasia": _obtener_valor_formulario(formulario, "nombre_fantasia"),
        "grupo_cliente_id": _obtener_valor_formulario(formulario, "grupo_cliente_id"),
        "telefono": _obtener_valor_formulario(formulario, "telefono"),
        "email": _obtener_valor_formulario(formulario, "email"),
        "domicilio": _obtener_valor_formulario(formulario, "domicilio"),
        "codigo_postal": _obtener_valor_formulario(formulario, "codigo_postal"),
        "ciudad": _obtener_valor_formulario(formulario, "ciudad"),
        "pais_id": _obtener_valor_formulario(formulario, "pais_id"),
        "provincia_id": _obtener_valor_formulario(formulario, "provincia_id"),
        "condicion_iva_codigo": _obtener_valor_formulario(
            formulario,
            "condicion_iva_codigo",
        ),
        "tipo_documento_fiscal_codigo": _obtener_valor_formulario(
            formulario,
            "tipo_documento_fiscal_codigo",
        ),
        "numero_documento_fiscal": _obtener_valor_formulario(
            formulario,
            "numero_documento_fiscal",
        ),
        "cuenta_deudores_ventas_codigo": _obtener_valor_formulario(
            formulario,
            "cuenta_deudores_ventas_codigo",
        ),
        "cuenta_anticipo_clientes_codigo": _obtener_valor_formulario(
            formulario,
            "cuenta_anticipo_clientes_codigo",
        ),
        "activo": _obtener_valor_checkbox_0_1(formulario, "activo"),
        "orden": _obtener_valor_formulario(formulario, "orden"),
        "observaciones": _obtener_valor_formulario(formulario, "observaciones"),
    }


def _validar_referencias_operativas_cliente(datos_cliente: dict[str, Any]) -> None:
    """Valida referencias activas antes de delegar persistencia al repository."""
    grupo_cliente_id = _normalizar_id_opcional(datos_cliente.get("grupo_cliente_id"))

    if grupo_cliente_id is None:
        raise ValueError("El grupo de clientes es obligatorio.")

    validar_grupo_cliente_activo(grupo_cliente_id)

    pais_id = _normalizar_id_opcional(datos_cliente.get("pais_id"))
    provincia_id = _normalizar_id_opcional(datos_cliente.get("provincia_id"))

    if provincia_id is not None and pais_id is None:
        raise ValueError("Para informar provincia tambien debe informarse pais.")

    if pais_id is not None:
        validar_pais_activo(pais_id)

    if provincia_id is not None:
        validar_provincia_activa(provincia_id)
        provincia = obtener_provincia_por_id(provincia_id)

        if provincia is None:
            raise ValueError("La provincia no existe o no esta activa.")

        if int(provincia["pais_id"]) != int(pais_id):
            raise ValueError("La provincia informada no pertenece al pais seleccionado.")

    condicion_iva_codigo = _normalizar_texto_opcional(
        datos_cliente.get("condicion_iva_codigo")
    )
    tipo_documento_fiscal_codigo = _normalizar_texto_opcional(
        datos_cliente.get("tipo_documento_fiscal_codigo")
    )

    if condicion_iva_codigo is not None:
        validar_item_catalogo_fiscal_activo("condiciones_iva", condicion_iva_codigo)

    if tipo_documento_fiscal_codigo is not None:
        validar_item_catalogo_fiscal_activo("tipos_documento", tipo_documento_fiscal_codigo)

    for campo in (
        "cuenta_deudores_ventas_codigo",
        "cuenta_anticipo_clientes_codigo",
    ):
        cuenta_codigo = _normalizar_texto_opcional(datos_cliente.get(campo))

        if cuenta_codigo is not None:
            validar_cuenta_contable_imputable(cuenta_codigo)


def _normalizar_id_opcional(valor: Any) -> int | None:
    valor_normalizado = str(valor or "").strip()

    if not valor_normalizado:
        return None

    try:
        valor_id = int(valor_normalizado)
    except ValueError as exc:
        raise ValueError("El id informado debe ser numerico.") from exc

    if valor_id <= 0:
        raise ValueError("El id informado debe ser positivo.")

    return valor_id


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
