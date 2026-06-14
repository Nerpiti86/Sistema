from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.shared.catalogos_fiscales_service import (
    activar_item_catalogo_fiscal,
    actualizar_item_catalogo_fiscal_desde_formulario,
    crear_item_catalogo_fiscal_desde_formulario,
    desactivar_item_catalogo_fiscal,
    obtener_contexto_detalle_catalogo_fiscal,
    obtener_contexto_listado_catalogo_fiscal,
)

bp = Blueprint(
    "tablas_comunes_fiscales",
    __name__,
    url_prefix="/tablas-comunes",
    template_folder="templates",
)


@bp.get("/condiciones-iva/")
def ver_listado_condiciones_iva():
    """Muestra listado del catalogo fiscal de condiciones frente al IVA."""
    contexto = obtener_contexto_listado_catalogo_fiscal(
        "condiciones_iva",
        "condiciones_iva",
    )

    return render_template(
        "tablas_comunes/condiciones_iva.html",
        page_title="Condiciones frente al IVA",
        **contexto,
    )


@bp.get("/condiciones-iva/nueva/")
def ver_formulario_nueva_condicion_iva():
    """Muestra formulario de alta manual de condicion frente al IVA."""
    return render_template(
        "tablas_comunes/condiciones_iva_form.html",
        page_title="Nueva condición frente al IVA",
        modo_formulario="alta",
        condicion_iva={"activo": 1, "orden": 0},
        action_url=url_for("tablas_comunes_fiscales.crear_condicion_iva_nueva"),
        form_titulo="Nueva condición frente al IVA",
        form_submit_label="Crear condición",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_condiciones_iva"),
        codigo_solo_lectura=False,
    )


@bp.post("/condiciones-iva/nueva/")
def crear_condicion_iva_nueva():
    """Crea una condicion frente al IVA desde formulario."""
    try:
        condicion_iva = crear_item_catalogo_fiscal_desde_formulario(
            "condiciones_iva",
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "tablas_comunes/condiciones_iva_form.html",
                page_title="Nueva condición frente al IVA",
                modo_formulario="alta",
                condicion_iva=request.form,
                action_url=url_for("tablas_comunes_fiscales.crear_condicion_iva_nueva"),
                form_titulo="Nueva condición frente al IVA",
                form_submit_label="Crear condición",
                form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_condiciones_iva"),
                codigo_solo_lectura=False,
            ),
            400,
        )

    flash("Condición frente al IVA creada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_condiciones_iva",
            condicion=condicion_iva["codigo"],
        )
    )


@bp.get("/condiciones-iva/<codigo_condicion_iva>/editar/")
def ver_formulario_editar_condicion_iva(codigo_condicion_iva):
    """Muestra formulario de edicion de condicion frente al IVA."""
    try:
        contexto = obtener_contexto_detalle_catalogo_fiscal(
            "condiciones_iva",
            codigo_condicion_iva,
            "condicion_iva",
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_condiciones_iva"))

    condicion_iva = contexto["condicion_iva"]
    titulo_formulario = (
        f"Editar condición frente al IVA {condicion_iva['codigo']} - "
        f"{condicion_iva['descripcion']}"
    )

    return render_template(
        "tablas_comunes/condiciones_iva_form.html",
        page_title=titulo_formulario,
        modo_formulario="edicion",
        condicion_iva=condicion_iva,
        action_url=url_for(
            "tablas_comunes_fiscales.actualizar_condicion_iva_existente",
            codigo_condicion_iva=condicion_iva["codigo"],
        ),
        form_titulo=titulo_formulario,
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_condiciones_iva"),
        codigo_solo_lectura=True,
    )


@bp.post("/condiciones-iva/<codigo_condicion_iva>/editar/")
def actualizar_condicion_iva_existente(codigo_condicion_iva):
    """Actualiza una condicion frente al IVA desde formulario."""
    try:
        condicion_iva = actualizar_item_catalogo_fiscal_desde_formulario(
            "condiciones_iva",
            codigo_condicion_iva,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        condicion_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        condicion_form["codigo"] = codigo_condicion_iva
        titulo_formulario = (
            f"Editar condición frente al IVA {codigo_condicion_iva} - "
            f"{condicion_form.get('descripcion', '')}"
        )
        return (
            render_template(
                "tablas_comunes/condiciones_iva_form.html",
                page_title=titulo_formulario,
                modo_formulario="edicion",
                condicion_iva=condicion_form,
                action_url=url_for(
                    "tablas_comunes_fiscales.actualizar_condicion_iva_existente",
                    codigo_condicion_iva=codigo_condicion_iva,
                ),
                form_titulo=titulo_formulario,
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_condiciones_iva"),
                codigo_solo_lectura=True,
            ),
            400,
        )

    flash("Condición frente al IVA actualizada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_condiciones_iva",
            condicion=condicion_iva["codigo"],
        )
    )


@bp.post("/condiciones-iva/<codigo_condicion_iva>/activar/")
def activar_condicion_iva_existente(codigo_condicion_iva):
    """Activa una condicion frente al IVA sin borrado fisico."""
    try:
        condicion_iva = activar_item_catalogo_fiscal("condiciones_iva", codigo_condicion_iva)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_condiciones_iva"))

    flash("Condición frente al IVA activada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_condiciones_iva",
            condicion=condicion_iva["codigo"],
        )
    )


@bp.post("/condiciones-iva/<codigo_condicion_iva>/desactivar/")
def desactivar_condicion_iva_existente(codigo_condicion_iva):
    """Desactiva una condicion frente al IVA sin borrado fisico."""
    try:
        condicion_iva = desactivar_item_catalogo_fiscal("condiciones_iva", codigo_condicion_iva)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_condiciones_iva"))

    flash("Condición frente al IVA desactivada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_condiciones_iva",
            condicion=condicion_iva["codigo"],
        )
    )


@bp.get("/tipos-documento/")
def ver_listado_tipos_documento():
    """Muestra listado del catalogo fiscal de tipos de documento."""
    contexto = obtener_contexto_listado_catalogo_fiscal(
        "tipos_documento",
        "tipos_documento",
    )

    return render_template(
        "tablas_comunes/tipos_documento.html",
        page_title="Tipos de documento",
        **contexto,
    )


@bp.get("/tipos-documento/nuevo/")
def ver_formulario_nuevo_tipo_documento():
    """Muestra formulario de alta manual de tipo de documento."""
    return render_template(
        "tablas_comunes/tipos_documento_form.html",
        page_title="Nuevo tipo de documento",
        modo_formulario="alta",
        tipo_documento={"activo": 1, "orden": 0},
        action_url=url_for("tablas_comunes_fiscales.crear_tipo_documento_nuevo"),
        form_titulo="Nuevo tipo de documento",
        form_submit_label="Crear tipo",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_tipos_documento"),
        codigo_solo_lectura=False,
    )


@bp.post("/tipos-documento/nuevo/")
def crear_tipo_documento_nuevo():
    """Crea un tipo de documento desde formulario."""
    try:
        tipo_documento = crear_item_catalogo_fiscal_desde_formulario(
            "tipos_documento",
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "tablas_comunes/tipos_documento_form.html",
                page_title="Nuevo tipo de documento",
                modo_formulario="alta",
                tipo_documento=request.form,
                action_url=url_for("tablas_comunes_fiscales.crear_tipo_documento_nuevo"),
                form_titulo="Nuevo tipo de documento",
                form_submit_label="Crear tipo",
                form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_tipos_documento"),
                codigo_solo_lectura=False,
            ),
            400,
        )

    flash("Tipo de documento creado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_documento",
            tipo=tipo_documento["codigo"],
        )
    )


@bp.get("/tipos-documento/<codigo_tipo_documento>/editar/")
def ver_formulario_editar_tipo_documento(codigo_tipo_documento):
    """Muestra formulario de edicion de tipo de documento."""
    try:
        contexto = obtener_contexto_detalle_catalogo_fiscal(
            "tipos_documento",
            codigo_tipo_documento,
            "tipo_documento",
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_documento"))

    tipo_documento = contexto["tipo_documento"]
    titulo_formulario = (
        f"Editar tipo de documento {tipo_documento['codigo']} - "
        f"{tipo_documento['descripcion']}"
    )

    return render_template(
        "tablas_comunes/tipos_documento_form.html",
        page_title=titulo_formulario,
        modo_formulario="edicion",
        tipo_documento=tipo_documento,
        action_url=url_for(
            "tablas_comunes_fiscales.actualizar_tipo_documento_existente",
            codigo_tipo_documento=tipo_documento["codigo"],
        ),
        form_titulo=titulo_formulario,
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_tipos_documento"),
        codigo_solo_lectura=True,
    )


@bp.post("/tipos-documento/<codigo_tipo_documento>/editar/")
def actualizar_tipo_documento_existente(codigo_tipo_documento):
    """Actualiza un tipo de documento desde formulario."""
    try:
        tipo_documento = actualizar_item_catalogo_fiscal_desde_formulario(
            "tipos_documento",
            codigo_tipo_documento,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        tipo_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        tipo_form["codigo"] = codigo_tipo_documento
        titulo_formulario = (
            f"Editar tipo de documento {codigo_tipo_documento} - "
            f"{tipo_form.get('descripcion', '')}"
        )
        return (
            render_template(
                "tablas_comunes/tipos_documento_form.html",
                page_title=titulo_formulario,
                modo_formulario="edicion",
                tipo_documento=tipo_form,
                action_url=url_for(
                    "tablas_comunes_fiscales.actualizar_tipo_documento_existente",
                    codigo_tipo_documento=codigo_tipo_documento,
                ),
                form_titulo=titulo_formulario,
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_tipos_documento"),
                codigo_solo_lectura=True,
            ),
            400,
        )

    flash("Tipo de documento actualizado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_documento",
            tipo=tipo_documento["codigo"],
        )
    )


@bp.post("/tipos-documento/<codigo_tipo_documento>/activar/")
def activar_tipo_documento_existente(codigo_tipo_documento):
    """Activa un tipo de documento sin borrado fisico."""
    try:
        tipo_documento = activar_item_catalogo_fiscal("tipos_documento", codigo_tipo_documento)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_documento"))

    flash("Tipo de documento activado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_documento",
            tipo=tipo_documento["codigo"],
        )
    )


@bp.post("/tipos-documento/<codigo_tipo_documento>/desactivar/")
def desactivar_tipo_documento_existente(codigo_tipo_documento):
    """Desactiva un tipo de documento sin borrado fisico."""
    try:
        tipo_documento = desactivar_item_catalogo_fiscal("tipos_documento", codigo_tipo_documento)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_documento"))

    flash("Tipo de documento desactivado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_documento",
            tipo=tipo_documento["codigo"],
        )
    )
