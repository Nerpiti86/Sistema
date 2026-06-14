from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.gestion.clientes_service import (
    activar_cliente,
    actualizar_cliente_desde_formulario,
    crear_cliente_desde_formulario,
    desactivar_cliente,
    obtener_contexto_detalle_cliente,
    obtener_contexto_formulario_cliente,
    obtener_contexto_listado_clientes,
)
from app.gestion.grupos_clientes_service import (
    activar_grupo_cliente,
    actualizar_grupo_cliente_desde_formulario,
    crear_grupo_cliente_desde_formulario,
    desactivar_grupo_cliente,
    obtener_contexto_detalle_grupo_cliente,
    obtener_contexto_listado_grupos_clientes,
)

bp = Blueprint(
    "gestion",
    __name__,
    url_prefix="/gestion",
    template_folder="templates",
)


@bp.get("/")
def index():
    """Redirige al primer maestro disponible de gestion."""
    return redirect(url_for("gestion.ver_listado_grupos_clientes"))


@bp.get("/clientes/")
def ver_listado_clientes():
    """Muestra listado del maestro de clientes."""
    contexto = obtener_contexto_listado_clientes()

    return render_template(
        "gestion/clientes.html",
        page_title="Clientes",
        **contexto,
    )


@bp.get("/clientes/nuevo/")
def ver_formulario_nuevo_cliente():
    """Muestra formulario de alta manual de cliente."""
    contexto_formulario = obtener_contexto_formulario_cliente()

    return render_template(
        "gestion/clientes_form.html",
        page_title="Nuevo cliente",
        modo_formulario="alta",
        action_url=url_for("gestion.crear_cliente_nuevo"),
        form_titulo="Nuevo cliente",
        form_submit_label="Crear cliente",
        form_cancelar_url=url_for("gestion.ver_listado_clientes"),
        **contexto_formulario,
    )


@bp.post("/clientes/nuevo/")
def crear_cliente_nuevo():
    """Crea un cliente desde formulario."""
    try:
        cliente = crear_cliente_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        contexto_formulario = obtener_contexto_formulario_cliente(
            _normalizar_formulario_para_template(request.form)
        )
        return (
            render_template(
                "gestion/clientes_form.html",
                page_title="Nuevo cliente",
                modo_formulario="alta",
                action_url=url_for("gestion.crear_cliente_nuevo"),
                form_titulo="Nuevo cliente",
                form_submit_label="Crear cliente",
                form_cancelar_url=url_for("gestion.ver_listado_clientes"),
                **contexto_formulario,
            ),
            400,
        )

    flash("Cliente creado correctamente.", "success")
    return redirect(url_for("gestion.ver_listado_clientes", cliente=cliente["id"]))


@bp.get("/clientes/<int:cliente_id>/editar/")
def ver_formulario_editar_cliente(cliente_id):
    """Muestra formulario de edicion de cliente."""
    try:
        contexto = obtener_contexto_detalle_cliente(cliente_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_clientes"))

    cliente = contexto["cliente"]
    contexto_formulario = obtener_contexto_formulario_cliente(cliente)

    return render_template(
        "gestion/clientes_form.html",
        page_title=f"Editar cliente {cliente['razon_social']}",
        modo_formulario="edicion",
        action_url=url_for(
            "gestion.actualizar_cliente_existente",
            cliente_id=cliente["id"],
        ),
        form_titulo=f"Editar cliente {cliente['razon_social']}",
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("gestion.ver_listado_clientes"),
        **contexto_formulario,
    )


@bp.post("/clientes/<int:cliente_id>/editar/")
def actualizar_cliente_existente(cliente_id):
    """Actualiza un cliente desde formulario."""
    try:
        cliente = actualizar_cliente_desde_formulario(cliente_id, request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        cliente_form = _normalizar_formulario_para_template(request.form)
        cliente_form["id"] = cliente_id
        contexto_formulario = obtener_contexto_formulario_cliente(cliente_form)

        return (
            render_template(
                "gestion/clientes_form.html",
                page_title=f"Editar cliente {cliente_id}",
                modo_formulario="edicion",
                action_url=url_for(
                    "gestion.actualizar_cliente_existente",
                    cliente_id=cliente_id,
                ),
                form_titulo=f"Editar cliente {cliente_id}",
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("gestion.ver_listado_clientes"),
                **contexto_formulario,
            ),
            400,
        )

    flash("Cliente actualizado correctamente.", "success")
    return redirect(url_for("gestion.ver_listado_clientes", cliente=cliente["id"]))


@bp.post("/clientes/<int:cliente_id>/activar/")
def activar_cliente_existente(cliente_id):
    """Activa un cliente sin borrado fisico."""
    try:
        cliente = activar_cliente(cliente_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_clientes"))

    flash("Cliente activado correctamente.", "success")
    return redirect(url_for("gestion.ver_listado_clientes", cliente=cliente["id"]))


@bp.post("/clientes/<int:cliente_id>/desactivar/")
def desactivar_cliente_existente(cliente_id):
    """Desactiva un cliente sin borrado fisico."""
    try:
        cliente = desactivar_cliente(cliente_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_clientes"))

    flash("Cliente desactivado correctamente.", "success")
    return redirect(url_for("gestion.ver_listado_clientes", cliente=cliente["id"]))


@bp.get("/clientes/grupos/")
def ver_listado_grupos_clientes():
    """Muestra listado del maestro de grupos de clientes."""
    contexto = obtener_contexto_listado_grupos_clientes()

    return render_template(
        "gestion/grupos_clientes.html",
        page_title="Grupos de clientes",
        **contexto,
    )


@bp.get("/clientes/grupos/nuevo/")
def ver_formulario_nuevo_grupo_cliente():
    """Muestra formulario de alta manual de grupo de clientes."""
    return render_template(
        "gestion/grupos_clientes_form.html",
        page_title="Nuevo grupo de clientes",
        modo_formulario="alta",
        grupo_cliente={"activo": 1, "orden": 0},
        action_url=url_for("gestion.crear_grupo_cliente_nuevo"),
        form_titulo="Nuevo grupo de clientes",
        form_submit_label="Crear grupo",
        form_cancelar_url=url_for("gestion.ver_listado_grupos_clientes"),
    )


@bp.post("/clientes/grupos/nuevo/")
def crear_grupo_cliente_nuevo():
    """Crea un grupo de clientes desde formulario."""
    try:
        grupo_cliente = crear_grupo_cliente_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "gestion/grupos_clientes_form.html",
                page_title="Nuevo grupo de clientes",
                modo_formulario="alta",
                grupo_cliente=request.form,
                action_url=url_for("gestion.crear_grupo_cliente_nuevo"),
                form_titulo="Nuevo grupo de clientes",
                form_submit_label="Crear grupo",
                form_cancelar_url=url_for("gestion.ver_listado_grupos_clientes"),
            ),
            400,
        )

    flash("Grupo de clientes creado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_listado_grupos_clientes",
            grupo=grupo_cliente["id"],
        )
    )


@bp.get("/clientes/grupos/<int:grupo_cliente_id>/editar/")
def ver_formulario_editar_grupo_cliente(grupo_cliente_id):
    """Muestra formulario de edicion de grupo de clientes."""
    try:
        contexto = obtener_contexto_detalle_grupo_cliente(grupo_cliente_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_grupos_clientes"))

    grupo_cliente = contexto["grupo_cliente"]

    return render_template(
        "gestion/grupos_clientes_form.html",
        page_title=f"Editar grupo de clientes {grupo_cliente['nombre']}",
        modo_formulario="edicion",
        grupo_cliente=grupo_cliente,
        action_url=url_for(
            "gestion.actualizar_grupo_cliente_existente",
            grupo_cliente_id=grupo_cliente["id"],
        ),
        form_titulo=f"Editar grupo de clientes {grupo_cliente['nombre']}",
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("gestion.ver_listado_grupos_clientes"),
    )


@bp.post("/clientes/grupos/<int:grupo_cliente_id>/editar/")
def actualizar_grupo_cliente_existente(grupo_cliente_id):
    """Actualiza un grupo de clientes desde formulario."""
    try:
        grupo_cliente = actualizar_grupo_cliente_desde_formulario(
            grupo_cliente_id,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        grupo_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        grupo_form["id"] = grupo_cliente_id

        return (
            render_template(
                "gestion/grupos_clientes_form.html",
                page_title=f"Editar grupo de clientes {grupo_cliente_id}",
                modo_formulario="edicion",
                grupo_cliente=grupo_form,
                action_url=url_for(
                    "gestion.actualizar_grupo_cliente_existente",
                    grupo_cliente_id=grupo_cliente_id,
                ),
                form_titulo=f"Editar grupo de clientes {grupo_cliente_id}",
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("gestion.ver_listado_grupos_clientes"),
            ),
            400,
        )

    flash("Grupo de clientes actualizado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_listado_grupos_clientes",
            grupo=grupo_cliente["id"],
        )
    )


@bp.post("/clientes/grupos/<int:grupo_cliente_id>/activar/")
def activar_grupo_cliente_existente(grupo_cliente_id):
    """Activa un grupo de clientes sin borrado fisico."""
    try:
        grupo_cliente = activar_grupo_cliente(grupo_cliente_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_grupos_clientes"))

    flash("Grupo de clientes activado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_listado_grupos_clientes",
            grupo=grupo_cliente["id"],
        )
    )


@bp.post("/clientes/grupos/<int:grupo_cliente_id>/desactivar/")
def desactivar_grupo_cliente_existente(grupo_cliente_id):
    """Desactiva un grupo de clientes sin borrado fisico."""
    try:
        grupo_cliente = desactivar_grupo_cliente(grupo_cliente_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_grupos_clientes"))

    flash("Grupo de clientes desactivado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_listado_grupos_clientes",
            grupo=grupo_cliente["id"],
        )
    )


def _normalizar_formulario_para_template(formulario) -> dict[str, str]:
    """Convierte request.form en dict simple para re-render de errores."""
    return {campo: formulario.get(campo, "") for campo in formulario.keys()}
