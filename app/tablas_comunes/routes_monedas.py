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


@bp.get("/monedas/")
def ver_listado_monedas():
    """Muestra listado del maestro transversal de monedas."""
    contexto_monedas = obtener_contexto_listado_monedas()

    return render_template(
        "tablas_comunes/monedas_abm.html",
        page_title="Monedas",
        **contexto_monedas,
    )


@bp.get("/monedas/nueva/")
def ver_formulario_nueva_moneda():
    """Muestra formulario de alta manual de moneda."""
    return render_template(
        "tablas_comunes/monedas_form.html",
        page_title="Nueva moneda",
        modo_formulario="alta",
        moneda={"activa": 1, "decimales": 2, "orden": 0},
        action_url=url_for("tablas_comunes.crear_moneda_nueva"),
        form_titulo="Nueva moneda",
        form_submit_label="Crear moneda",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_monedas"),
        codigo_solo_lectura=False,
    )


@bp.post("/monedas/nueva/")
def crear_moneda_nueva():
    """Crea una moneda manual desde formulario."""
    try:
        moneda = crear_moneda_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "tablas_comunes/monedas_form.html",
                page_title="Nueva moneda",
                modo_formulario="alta",
                moneda=request.form,
                action_url=url_for("tablas_comunes.crear_moneda_nueva"),
                form_titulo="Nueva moneda",
                form_submit_label="Crear moneda",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_monedas"),
                codigo_solo_lectura=False,
            ),
            400,
        )

    flash("Moneda creada correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_monedas", moneda=moneda["codigo"]))


@bp.get("/monedas/<codigo_moneda>/editar/")
def ver_formulario_editar_moneda(codigo_moneda):
    """Muestra formulario de edicion de moneda."""
    try:
        contexto_moneda = obtener_contexto_detalle_moneda(codigo_moneda)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_monedas"))

    moneda = contexto_moneda["moneda"]

    return render_template(
        "tablas_comunes/monedas_form.html",
        page_title=f"Editar moneda {moneda['codigo']}",
        modo_formulario="edicion",
        moneda=moneda,
        action_url=url_for(
            "tablas_comunes.actualizar_moneda_existente",
            codigo_moneda=moneda["codigo"],
        ),
        form_titulo=f"Editar moneda {moneda['codigo']}",
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes.ver_listado_monedas"),
        codigo_solo_lectura=True,
    )


@bp.post("/monedas/<codigo_moneda>/editar/")
def actualizar_moneda_existente(codigo_moneda):
    """Actualiza una moneda desde formulario."""
    try:
        moneda = actualizar_moneda_desde_formulario(codigo_moneda, request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        moneda_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        moneda_form["codigo"] = codigo_moneda

        return (
            render_template(
                "tablas_comunes/monedas_form.html",
                page_title=f"Editar moneda {codigo_moneda}",
                modo_formulario="edicion",
                moneda=moneda_form,
                action_url=url_for(
                    "tablas_comunes.actualizar_moneda_existente",
                    codigo_moneda=codigo_moneda,
                ),
                form_titulo=f"Editar moneda {codigo_moneda}",
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("tablas_comunes.ver_listado_monedas"),
                codigo_solo_lectura=True,
            ),
            400,
        )

    flash("Moneda actualizada correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_monedas", moneda=moneda["codigo"]))


@bp.post("/monedas/<codigo_moneda>/activar/")
def activar_moneda_existente(codigo_moneda):
    """Activa una moneda sin borrado fisico."""
    try:
        moneda = activar_moneda(codigo_moneda)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_monedas"))

    flash("Moneda activada correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_monedas", moneda=moneda["codigo"]))


@bp.post("/monedas/<codigo_moneda>/desactivar/")
def desactivar_moneda_existente(codigo_moneda):
    """Desactiva una moneda sin borrado fisico."""
    try:
        moneda = desactivar_moneda(codigo_moneda)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes.ver_listado_monedas"))

    flash("Moneda desactivada correctamente.", "success")
    return redirect(url_for("tablas_comunes.ver_listado_monedas", moneda=moneda["codigo"]))
