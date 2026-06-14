from flask import flash, redirect, render_template, request, url_for

from app.shared.bancos_service import (
    activar_banco,
    actualizar_banco_desde_formulario,
    crear_banco_desde_formulario,
    desactivar_banco,
    obtener_contexto_detalle_banco,
    obtener_contexto_listado_bancos,
)
from app.shared.medios_operativos_service import (
    activar_medio_operativo,
    actualizar_medio_operativo_desde_formulario,
    crear_medio_operativo_desde_formulario,
    desactivar_medio_operativo,
    obtener_contexto_detalle_medio_operativo,
    obtener_contexto_formulario_medio_operativo,
    obtener_contexto_listado_medios_operativos,
)
from app.shared.monedas_service import (
    activar_moneda,
    actualizar_moneda_desde_formulario,
    crear_moneda_desde_formulario,
    desactivar_moneda,
    obtener_contexto_detalle_moneda,
    obtener_contexto_listado_monedas,
)
from app.shared.paises_service import (
    activar_pais,
    actualizar_pais_desde_formulario,
    crear_pais_desde_formulario,
    desactivar_pais,
    obtener_contexto_detalle_pais,
    obtener_contexto_listado_paises,
)
from app.shared.provincias_service import (
    activar_provincia,
    actualizar_provincia_desde_formulario,
    crear_provincia_desde_formulario,
    desactivar_provincia,
    obtener_contexto_detalle_provincia,
    obtener_contexto_formulario_provincia,
    obtener_contexto_listado_provincias,
)
from app.tablas_comunes.blueprint import bp


@bp.get("/medios-operativos/")
def ver_listado_medios_operativos():
    """Muestra listado del maestro transversal de medios operativos."""
    contexto = obtener_contexto_listado_medios_operativos()

    return render_template(
        "tablas_comunes/medios_operativos.html",
        page_title="Medios operativos",
        **contexto,
    )


@bp.get("/medios-operativos/nuevo/")
def ver_formulario_nuevo_medio_operativo():
    """Muestra formulario de alta manual de medio operativo."""
    contexto = obtener_contexto_formulario_medio_operativo()

    return render_template(
        "tablas_comunes/medios_operativos_form.html",
        page_title="Nuevo medio operativo",
        modo_formulario="alta",
        action_url=url_for("tablas_comunes.crear_medio_operativo_nuevo"),
        form_titulo="Nuevo medio operativo",
        form_submit_label="Crear medio operativo",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_medios_operativos"),
        codigo_solo_lectura=False,
        **contexto,
    )


@bp.post("/medios-operativos/nuevo/")
def crear_medio_operativo_nuevo():
    """Crea un medio operativo manual desde formulario."""
    try:
        medio_operativo = crear_medio_operativo_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        contexto = obtener_contexto_formulario_medio_operativo(dict(request.form))
        return (
            render_template(
                "tablas_comunes/medios_operativos_form.html",
                page_title="Nuevo medio operativo",
                modo_formulario="alta",
                action_url=url_for("tablas_comunes.crear_medio_operativo_nuevo"),
                form_titulo="Nuevo medio operativo",
                form_submit_label="Crear medio operativo",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_medios_operativos"),
                codigo_solo_lectura=False,
                **contexto,
            ),
            400,
        )

    flash("Medio operativo creado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes.ver_listado_medios_operativos",
            medio=medio_operativo["codigo"],
        )
    )


@bp.get("/medios-operativos/<codigo_medio_operativo>/editar/")
def ver_formulario_editar_medio_operativo(codigo_medio_operativo):
    """Muestra formulario de edicion de medio operativo."""
    try:
        contexto_detalle = obtener_contexto_detalle_medio_operativo(
            codigo_medio_operativo
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_medios_operativos"))

    contexto = obtener_contexto_formulario_medio_operativo(
        contexto_detalle["medio_operativo"]
    )
    medio_operativo = contexto["medio_operativo"]
    titulo_formulario = (
        f"Editar medio operativo {medio_operativo['codigo']} - "
        f"{medio_operativo['nombre']}"
    )

    return render_template(
        "tablas_comunes/medios_operativos_form.html",
        page_title=titulo_formulario,
        modo_formulario="edicion",
        action_url=url_for(
            "tablas_comunes.actualizar_medio_operativo_existente",
            codigo_medio_operativo=codigo_medio_operativo,
        ),
        form_titulo=titulo_formulario,
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_medios_operativos"),
        codigo_solo_lectura=True,
        **contexto,
    )


@bp.post("/medios-operativos/<codigo_medio_operativo>/editar/")
def actualizar_medio_operativo_existente(codigo_medio_operativo):
    """Actualiza un medio operativo desde formulario."""
    try:
        medio_operativo = actualizar_medio_operativo_desde_formulario(
            codigo_medio_operativo,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        medio_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        medio_form["codigo"] = codigo_medio_operativo
        contexto = obtener_contexto_formulario_medio_operativo(medio_form)
        medio_operativo = contexto["medio_operativo"]
        titulo_formulario = (
            f"Editar medio operativo {medio_operativo['codigo']} - "
            f"{medio_operativo.get('nombre', '')}"
        )
        return (
            render_template(
                "tablas_comunes/medios_operativos_form.html",
                page_title=titulo_formulario,
                modo_formulario="edicion",
                action_url=url_for(
                    "tablas_comunes.actualizar_medio_operativo_existente",
                    codigo_medio_operativo=codigo_medio_operativo,
                ),
                form_titulo=titulo_formulario,
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_medios_operativos"),
                codigo_solo_lectura=True,
                **contexto,
            ),
            400,
        )

    flash("Medio operativo actualizado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes.ver_listado_medios_operativos",
            medio=medio_operativo["codigo"],
        )
    )


@bp.post("/medios-operativos/<codigo_medio_operativo>/activar/")
def activar_medio_operativo_existente(codigo_medio_operativo):
    """Activa un medio operativo sin borrado fisico."""
    try:
        medio_operativo = activar_medio_operativo(codigo_medio_operativo)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_medios_operativos"))

    flash("Medio operativo activado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes.ver_listado_medios_operativos",
            medio=medio_operativo["codigo"],
        )
    )


@bp.post("/medios-operativos/<codigo_medio_operativo>/desactivar/")
def desactivar_medio_operativo_existente(codigo_medio_operativo):
    """Desactiva un medio operativo sin borrado fisico."""
    try:
        medio_operativo = desactivar_medio_operativo(codigo_medio_operativo)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_medios_operativos"))

    flash("Medio operativo desactivado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes.ver_listado_medios_operativos",
            medio=medio_operativo["codigo"],
        )
    )
