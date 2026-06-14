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


@bp.get("/provincias/")
def ver_listado_provincias():
    """Muestra listado del maestro transversal de provincias."""
    contexto_provincias = obtener_contexto_listado_provincias()

    return render_template(
        "tablas_comunes/provincias.html",
        page_title="Provincias",
        **contexto_provincias,
    )


@bp.get("/provincias/nuevo/")
def ver_formulario_nueva_provincia():
    """Muestra formulario de alta manual de provincia."""
    contexto = obtener_contexto_formulario_provincia()

    return render_template(
        "tablas_comunes/provincias_form.html",
        page_title="Nueva provincia",
        modo_formulario="alta",
        action_url=url_for("tablas_comunes.crear_provincia_nueva"),
        form_titulo="Nueva provincia",
        form_submit_label="Crear provincia",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_provincias"),
        **contexto,
    )


@bp.post("/provincias/nuevo/")
def crear_provincia_nueva():
    """Crea una provincia manual desde formulario."""
    try:
        provincia = crear_provincia_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        provincia_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        contexto = obtener_contexto_formulario_provincia(provincia_form)

        return (
            render_template(
                "tablas_comunes/provincias_form.html",
                page_title="Nueva provincia",
                modo_formulario="alta",
                action_url=url_for("tablas_comunes.crear_provincia_nueva"),
                form_titulo="Nueva provincia",
                form_submit_label="Crear provincia",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_provincias"),
                **contexto,
            ),
            400,
        )

    flash("Provincia creada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes.ver_listado_provincias",
            provincia=provincia["id"],
        )
    )


@bp.get("/provincias/<int:provincia_id>/editar/")
def ver_formulario_editar_provincia(provincia_id):
    """Muestra formulario de edicion de provincia."""
    try:
        contexto_detalle = obtener_contexto_detalle_provincia(provincia_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_provincias"))

    contexto = obtener_contexto_formulario_provincia(contexto_detalle["provincia"])
    provincia = contexto["provincia"]

    return render_template(
        "tablas_comunes/provincias_form.html",
        page_title=f"Editar provincia {provincia['nombre']}",
        modo_formulario="edicion",
        action_url=url_for(
            "tablas_comunes.actualizar_provincia_existente",
            provincia_id=provincia["id"],
        ),
        form_titulo=f"Editar provincia {provincia['nombre']}",
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_provincias"),
        **contexto,
    )


@bp.post("/provincias/<int:provincia_id>/editar/")
def actualizar_provincia_existente(provincia_id):
    """Actualiza una provincia desde formulario."""
    try:
        provincia = actualizar_provincia_desde_formulario(provincia_id, request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        provincia_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        provincia_form["id"] = provincia_id
        contexto = obtener_contexto_formulario_provincia(provincia_form)

        return (
            render_template(
                "tablas_comunes/provincias_form.html",
                page_title=f"Editar provincia {provincia_id}",
                modo_formulario="edicion",
                action_url=url_for(
                    "tablas_comunes.actualizar_provincia_existente",
                    provincia_id=provincia_id,
                ),
                form_titulo=f"Editar provincia {provincia_id}",
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_provincias"),
                **contexto,
            ),
            400,
        )

    flash("Provincia actualizada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes.ver_listado_provincias",
            provincia=provincia["id"],
        )
    )


@bp.post("/provincias/<int:provincia_id>/activar/")
def activar_provincia_existente(provincia_id):
    """Activa una provincia sin borrado fisico."""
    try:
        provincia = activar_provincia(provincia_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_provincias"))

    flash("Provincia activada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes.ver_listado_provincias",
            provincia=provincia["id"],
        )
    )


@bp.post("/provincias/<int:provincia_id>/desactivar/")
def desactivar_provincia_existente(provincia_id):
    """Desactiva una provincia sin borrado fisico."""
    try:
        provincia = desactivar_provincia(provincia_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_provincias"))

    flash("Provincia desactivada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes.ver_listado_provincias",
            provincia=provincia["id"],
        )
    )
