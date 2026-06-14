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


@bp.get("/paises/")
def ver_listado_paises():
    """Muestra listado del maestro transversal de paises."""
    contexto_paises = obtener_contexto_listado_paises()

    return render_template(
        "tablas_comunes/paises.html",
        page_title="Países",
        **contexto_paises,
    )


@bp.get("/paises/nuevo/")
def ver_formulario_nuevo_pais():
    """Muestra formulario de alta manual de pais."""
    return render_template(
        "tablas_comunes/paises_form.html",
        page_title="Nuevo país",
        modo_formulario="alta",
        pais={"activo": 1, "orden": 0},
        action_url=url_for("tablas_comunes.crear_pais_nuevo"),
        form_titulo="Nuevo país",
        form_submit_label="Crear país",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_paises"),
    )


@bp.post("/paises/nuevo/")
def crear_pais_nuevo():
    """Crea un pais manual desde formulario."""
    try:
        pais = crear_pais_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "tablas_comunes/paises_form.html",
                page_title="Nuevo país",
                modo_formulario="alta",
                pais=request.form,
                action_url=url_for("tablas_comunes.crear_pais_nuevo"),
                form_titulo="Nuevo país",
                form_submit_label="Crear país",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_paises"),
            ),
            400,
        )

    flash("País creado correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_paises", pais=pais["id"]))


@bp.get("/paises/<int:pais_id>/editar/")
def ver_formulario_editar_pais(pais_id):
    """Muestra formulario de edicion de pais."""
    try:
        contexto_pais = obtener_contexto_detalle_pais(pais_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_paises"))

    pais = contexto_pais["pais"]

    return render_template(
        "tablas_comunes/paises_form.html",
        page_title=f"Editar país {pais['nombre']}",
        modo_formulario="edicion",
        pais=pais,
        action_url=url_for(
            "tablas_comunes.actualizar_pais_existente",
            pais_id=pais["id"],
        ),
        form_titulo=f"Editar país {pais['nombre']}",
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_paises"),
    )


@bp.post("/paises/<int:pais_id>/editar/")
def actualizar_pais_existente(pais_id):
    """Actualiza un pais desde formulario."""
    try:
        pais = actualizar_pais_desde_formulario(pais_id, request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        pais_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        pais_form["id"] = pais_id

        return (
            render_template(
                "tablas_comunes/paises_form.html",
                page_title=f"Editar país {pais_id}",
                modo_formulario="edicion",
                pais=pais_form,
                action_url=url_for(
                    "tablas_comunes.actualizar_pais_existente",
                    pais_id=pais_id,
                ),
                form_titulo=f"Editar país {pais_id}",
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_paises"),
            ),
            400,
        )

    flash("País actualizado correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_paises", pais=pais["id"]))


@bp.post("/paises/<int:pais_id>/activar/")
def activar_pais_existente(pais_id):
    """Activa un pais sin borrado fisico."""
    try:
        pais = activar_pais(pais_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_paises"))

    flash("País activado correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_paises", pais=pais["id"]))


@bp.post("/paises/<int:pais_id>/desactivar/")
def desactivar_pais_existente(pais_id):
    """Desactiva un pais sin borrado fisico."""
    try:
        pais = desactivar_pais(pais_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_paises"))

    flash("País desactivado correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_paises", pais=pais["id"]))
