from flask import Blueprint, flash, redirect, render_template, request, url_for

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


@bp.get("/bancos/")
def ver_listado_bancos():
    """Muestra listado del maestro transversal de bancos."""
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
