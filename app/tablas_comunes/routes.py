from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.shared.bancos_service import (
    activar_banco,
    actualizar_banco_desde_formulario,
    crear_banco_desde_formulario,
    desactivar_banco,
    obtener_contexto_detalle_banco,
    obtener_contexto_listado_bancos,
)
from app.shared.monedas_service import obtener_contexto_listado_monedas

bp = Blueprint(
    "tablas_comunes",
    __name__,
    url_prefix="/tablas-comunes",
    template_folder="templates",
)


@bp.get("/")
def index():
    """Redirige al primer maestro de tablas comunes."""
    return redirect(url_for("tablas_comunes.ver_listado_monedas"))


@bp.get("/monedas/")
def ver_listado_monedas():
    """
    Muestra listado del maestro transversal de monedas.

    Esta route no ejecuta SQL directo. El contexto de pantalla queda delegado
    al service transversal de monedas.
    """
    contexto_monedas = obtener_contexto_listado_monedas()

    return render_template(
        "tablas_comunes/monedas.html",
        page_title="Monedas",
        **contexto_monedas,
    )


@bp.get("/bancos/")
def ver_listado_bancos():
    """
    Muestra listado del maestro transversal de bancos.

    Esta route no ejecuta SQL directo. El contexto de pantalla queda delegado
    al service transversal de bancos.
    """
    contexto_bancos = obtener_contexto_listado_bancos()

    return render_template(
        "tablas_comunes/bancos.html",
        page_title="Bancos",
        **contexto_bancos,
    )


@bp.get("/bancos/nuevo/")
def ver_formulario_nuevo_banco():
    """Muestra formulario de alta manual de banco."""
    return render_template(
        "tablas_comunes/bancos_form.html",
        page_title="Nuevo banco",
        modo_formulario="alta",
        banco={"activo": 1, "orden": 0},
        action_url=url_for("tablas_comunes.crear_banco_nuevo"),
        form_titulo="Nuevo banco",
        form_submit_label="Crear banco",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_bancos"),
        codigo_solo_lectura=False,
    )


@bp.post("/bancos/nuevo/")
def crear_banco_nuevo():
    """Crea un banco manual desde formulario."""
    try:
        banco = crear_banco_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "tablas_comunes/bancos_form.html",
                page_title="Nuevo banco",
                modo_formulario="alta",
                banco=request.form,
                action_url=url_for("tablas_comunes.crear_banco_nuevo"),
                form_titulo="Nuevo banco",
                form_submit_label="Crear banco",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_bancos"),
                codigo_solo_lectura=False,
            ),
            400,
        )

    flash("Banco creado correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_bancos", banco=banco["codigo"]))


@bp.get("/bancos/<codigo_banco>/editar/")
def ver_formulario_editar_banco(codigo_banco):
    """Muestra formulario de edicion de banco."""
    try:
        contexto_banco = obtener_contexto_detalle_banco(codigo_banco)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_bancos"))

    banco = contexto_banco["banco"]

    return render_template(
        "tablas_comunes/bancos_form.html",
        page_title=f"Editar banco {banco['codigo']}",
        modo_formulario="edicion",
        banco=banco,
        action_url=url_for(
            "tablas_comunes.actualizar_banco_existente",
            codigo_banco=banco["codigo"],
        ),
        form_titulo=f"Editar banco {banco['codigo']}",
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_bancos"),
        codigo_solo_lectura=True,
    )


@bp.post("/bancos/<codigo_banco>/editar/")
def actualizar_banco_existente(codigo_banco):
    """Actualiza un banco desde formulario."""
    try:
        banco = actualizar_banco_desde_formulario(codigo_banco, request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        banco_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        banco_form["codigo"] = codigo_banco

        return (
            render_template(
                "tablas_comunes/bancos_form.html",
                page_title=f"Editar banco {codigo_banco}",
                modo_formulario="edicion",
                banco=banco_form,
                action_url=url_for(
                    "tablas_comunes.actualizar_banco_existente",
                    codigo_banco=codigo_banco,
                ),
                form_titulo=f"Editar banco {codigo_banco}",
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_bancos"),
                codigo_solo_lectura=True,
            ),
            400,
        )

    flash("Banco actualizado correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_bancos", banco=banco["codigo"]))


@bp.post("/bancos/<codigo_banco>/activar/")
def activar_banco_existente(codigo_banco):
    """Activa un banco sin borrado fisico."""
    try:
        banco = activar_banco(codigo_banco)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_bancos"))

    flash("Banco activado correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_bancos", banco=banco["codigo"]))


@bp.post("/bancos/<codigo_banco>/desactivar/")
def desactivar_banco_existente(codigo_banco):
    """Desactiva un banco sin borrado fisico."""
    try:
        banco = desactivar_banco(codigo_banco)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_bancos"))

    flash("Banco desactivado correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_bancos", banco=banco["codigo"]))
