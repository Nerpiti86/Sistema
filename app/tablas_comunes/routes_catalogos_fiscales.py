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


@bp.get("/unidades-medida/")
def ver_listado_unidades_medida():
    """Muestra listado del catalogo fiscal de unidades de medida."""
    contexto = obtener_contexto_listado_catalogo_fiscal(
        "unidades_medida",
        "unidades_medida",
    )

    return render_template(
        "tablas_comunes/unidades_medida.html",
        page_title="Unidades de medida",
        **contexto,
    )


@bp.get("/unidades-medida/nueva/")
def ver_formulario_nueva_unidad_medida():
    """Muestra formulario de alta manual de unidad de medida."""
    return render_template(
        "tablas_comunes/unidades_medida_form.html",
        page_title="Nueva unidad de medida",
        modo_formulario="alta",
        unidad_medida={"activo": 1, "orden": 0},
        action_url=url_for("tablas_comunes_fiscales.crear_unidad_medida_nueva"),
        form_titulo="Nueva unidad de medida",
        form_submit_label="Crear unidad",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_unidades_medida"),
        codigo_solo_lectura=False,
    )


@bp.post("/unidades-medida/nueva/")
def crear_unidad_medida_nueva():
    """Crea una unidad de medida desde formulario."""
    try:
        unidad_medida = crear_item_catalogo_fiscal_desde_formulario(
            "unidades_medida",
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "tablas_comunes/unidades_medida_form.html",
                page_title="Nueva unidad de medida",
                modo_formulario="alta",
                unidad_medida=request.form,
                action_url=url_for("tablas_comunes_fiscales.crear_unidad_medida_nueva"),
                form_titulo="Nueva unidad de medida",
                form_submit_label="Crear unidad",
                form_cancelar_url=url_for(
                    "tablas_comunes_fiscales.ver_listado_unidades_medida"
                ),
                codigo_solo_lectura=False,
            ),
            400,
        )

    flash("Unidad de medida creada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_unidades_medida",
            unidad=unidad_medida["codigo"],
        )
    )


@bp.get("/unidades-medida/<codigo_unidad_medida>/editar/")
def ver_formulario_editar_unidad_medida(codigo_unidad_medida):
    """Muestra formulario de edicion de unidad de medida."""
    try:
        contexto = obtener_contexto_detalle_catalogo_fiscal(
            "unidades_medida",
            codigo_unidad_medida,
            "unidad_medida",
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_unidades_medida"))

    unidad_medida = contexto["unidad_medida"]
    titulo_formulario = (
        f"Editar unidad de medida {unidad_medida['codigo']} - "
        f"{unidad_medida['descripcion']}"
    )

    return render_template(
        "tablas_comunes/unidades_medida_form.html",
        page_title=titulo_formulario,
        modo_formulario="edicion",
        unidad_medida=unidad_medida,
        action_url=url_for(
            "tablas_comunes_fiscales.actualizar_unidad_medida_existente",
            codigo_unidad_medida=unidad_medida["codigo"],
        ),
        form_titulo=titulo_formulario,
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_unidades_medida"),
        codigo_solo_lectura=True,
    )


@bp.post("/unidades-medida/<codigo_unidad_medida>/editar/")
def actualizar_unidad_medida_existente(codigo_unidad_medida):
    """Actualiza una unidad de medida desde formulario."""
    try:
        unidad_medida = actualizar_item_catalogo_fiscal_desde_formulario(
            "unidades_medida",
            codigo_unidad_medida,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        unidad_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        unidad_form["codigo"] = codigo_unidad_medida
        titulo_formulario = (
            f"Editar unidad de medida {codigo_unidad_medida} - "
            f"{unidad_form.get('descripcion', '')}"
        )
        return (
            render_template(
                "tablas_comunes/unidades_medida_form.html",
                page_title=titulo_formulario,
                modo_formulario="edicion",
                unidad_medida=unidad_form,
                action_url=url_for(
                    "tablas_comunes_fiscales.actualizar_unidad_medida_existente",
                    codigo_unidad_medida=codigo_unidad_medida,
                ),
                form_titulo=titulo_formulario,
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for(
                    "tablas_comunes_fiscales.ver_listado_unidades_medida"
                ),
                codigo_solo_lectura=True,
            ),
            400,
        )

    flash("Unidad de medida actualizada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_unidades_medida",
            unidad=unidad_medida["codigo"],
        )
    )


@bp.post("/unidades-medida/<codigo_unidad_medida>/activar/")
def activar_unidad_medida_existente(codigo_unidad_medida):
    """Activa una unidad de medida sin borrado fisico."""
    try:
        unidad_medida = activar_item_catalogo_fiscal("unidades_medida", codigo_unidad_medida)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_unidades_medida"))

    flash("Unidad de medida activada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_unidades_medida",
            unidad=unidad_medida["codigo"],
        )
    )


@bp.post("/unidades-medida/<codigo_unidad_medida>/desactivar/")
def desactivar_unidad_medida_existente(codigo_unidad_medida):
    """Desactiva una unidad de medida sin borrado fisico."""
    try:
        unidad_medida = desactivar_item_catalogo_fiscal("unidades_medida", codigo_unidad_medida)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_unidades_medida"))

    flash("Unidad de medida desactivada correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_unidades_medida",
            unidad=unidad_medida["codigo"],
        )
    )


@bp.get("/tipos-bonificacion/")
def ver_listado_tipos_bonificacion():
    """Muestra listado del catalogo fiscal de tipos de bonificacion."""
    contexto = obtener_contexto_listado_catalogo_fiscal(
        "tipos_bonificacion",
        "tipos_bonificacion",
    )

    return render_template(
        "tablas_comunes/tipos_bonificacion.html",
        page_title="Tipos de bonificación",
        **contexto,
    )


@bp.get("/tipos-bonificacion/nuevo/")
def ver_formulario_nuevo_tipo_bonificacion():
    """Muestra formulario de alta manual de tipo de bonificacion."""
    return render_template(
        "tablas_comunes/tipos_bonificacion_form.html",
        page_title="Nuevo tipo de bonificación",
        modo_formulario="alta",
        tipo_bonificacion={"activo": 1, "orden": 0},
        action_url=url_for("tablas_comunes_fiscales.crear_tipo_bonificacion_nuevo"),
        form_titulo="Nuevo tipo de bonificación",
        form_submit_label="Crear tipo",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_tipos_bonificacion"),
        codigo_solo_lectura=False,
    )


@bp.post("/tipos-bonificacion/nuevo/")
def crear_tipo_bonificacion_nuevo():
    """Crea un tipo de bonificacion desde formulario."""
    try:
        tipo_bonificacion = crear_item_catalogo_fiscal_desde_formulario(
            "tipos_bonificacion",
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "tablas_comunes/tipos_bonificacion_form.html",
                page_title="Nuevo tipo de bonificación",
                modo_formulario="alta",
                tipo_bonificacion=request.form,
                action_url=url_for("tablas_comunes_fiscales.crear_tipo_bonificacion_nuevo"),
                form_titulo="Nuevo tipo de bonificación",
                form_submit_label="Crear tipo",
                form_cancelar_url=url_for(
                    "tablas_comunes_fiscales.ver_listado_tipos_bonificacion"
                ),
                codigo_solo_lectura=False,
            ),
            400,
        )

    flash("Tipo de bonificación creado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_bonificacion",
            tipo=tipo_bonificacion["codigo"],
        )
    )


@bp.get("/tipos-bonificacion/<codigo_tipo_bonificacion>/editar/")
def ver_formulario_editar_tipo_bonificacion(codigo_tipo_bonificacion):
    """Muestra formulario de edicion de tipo de bonificacion."""
    try:
        contexto = obtener_contexto_detalle_catalogo_fiscal(
            "tipos_bonificacion",
            codigo_tipo_bonificacion,
            "tipo_bonificacion",
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_bonificacion"))

    tipo_bonificacion = contexto["tipo_bonificacion"]
    titulo_formulario = (
        f"Editar tipo de bonificación {tipo_bonificacion['codigo']} - "
        f"{tipo_bonificacion['descripcion']}"
    )

    return render_template(
        "tablas_comunes/tipos_bonificacion_form.html",
        page_title=titulo_formulario,
        modo_formulario="edicion",
        tipo_bonificacion=tipo_bonificacion,
        action_url=url_for(
            "tablas_comunes_fiscales.actualizar_tipo_bonificacion_existente",
            codigo_tipo_bonificacion=tipo_bonificacion["codigo"],
        ),
        form_titulo=titulo_formulario,
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_tipos_bonificacion"),
        codigo_solo_lectura=True,
    )


@bp.post("/tipos-bonificacion/<codigo_tipo_bonificacion>/editar/")
def actualizar_tipo_bonificacion_existente(codigo_tipo_bonificacion):
    """Actualiza un tipo de bonificacion desde formulario."""
    try:
        tipo_bonificacion = actualizar_item_catalogo_fiscal_desde_formulario(
            "tipos_bonificacion",
            codigo_tipo_bonificacion,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        tipo_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        tipo_form["codigo"] = codigo_tipo_bonificacion
        titulo_formulario = (
            f"Editar tipo de bonificación {codigo_tipo_bonificacion} - "
            f"{tipo_form.get('descripcion', '')}"
        )
        return (
            render_template(
                "tablas_comunes/tipos_bonificacion_form.html",
                page_title=titulo_formulario,
                modo_formulario="edicion",
                tipo_bonificacion=tipo_form,
                action_url=url_for(
                    "tablas_comunes_fiscales.actualizar_tipo_bonificacion_existente",
                    codigo_tipo_bonificacion=codigo_tipo_bonificacion,
                ),
                form_titulo=titulo_formulario,
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for(
                    "tablas_comunes_fiscales.ver_listado_tipos_bonificacion"
                ),
                codigo_solo_lectura=True,
            ),
            400,
        )

    flash("Tipo de bonificación actualizado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_bonificacion",
            tipo=tipo_bonificacion["codigo"],
        )
    )


@bp.post("/tipos-bonificacion/<codigo_tipo_bonificacion>/activar/")
def activar_tipo_bonificacion_existente(codigo_tipo_bonificacion):
    """Activa un tipo de bonificacion sin borrado fisico."""
    try:
        tipo_bonificacion = activar_item_catalogo_fiscal(
            "tipos_bonificacion",
            codigo_tipo_bonificacion,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_bonificacion"))

    flash("Tipo de bonificación activado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_bonificacion",
            tipo=tipo_bonificacion["codigo"],
        )
    )


@bp.post("/tipos-bonificacion/<codigo_tipo_bonificacion>/desactivar/")
def desactivar_tipo_bonificacion_existente(codigo_tipo_bonificacion):
    """Desactiva un tipo de bonificacion sin borrado fisico."""
    try:
        tipo_bonificacion = desactivar_item_catalogo_fiscal(
            "tipos_bonificacion",
            codigo_tipo_bonificacion,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_bonificacion"))

    flash("Tipo de bonificación desactivado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_bonificacion",
            tipo=tipo_bonificacion["codigo"],
        )
    )


@bp.get("/tipos-comprobante/")
def ver_listado_tipos_comprobante():
    """Muestra listado del catalogo fiscal de tipos de comprobante."""
    contexto = obtener_contexto_listado_catalogo_fiscal(
        "tipos_comprobante",
        "tipos_comprobante",
    )

    return render_template(
        "tablas_comunes/tipos_comprobante.html",
        page_title="Tipos de comprobantes",
        **contexto,
    )


@bp.get("/tipos-comprobante/nuevo/")
def ver_formulario_nuevo_tipo_comprobante():
    """Muestra formulario de alta manual de tipo de comprobante."""
    return render_template(
        "tablas_comunes/tipos_comprobante_form.html",
        page_title="Nuevo tipo de comprobante",
        modo_formulario="alta",
        tipo_comprobante={"activo": 1, "orden": 0},
        action_url=url_for("tablas_comunes_fiscales.crear_tipo_comprobante_nuevo"),
        form_titulo="Nuevo tipo de comprobante",
        form_submit_label="Crear tipo",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_tipos_comprobante"),
        codigo_solo_lectura=False,
    )


@bp.post("/tipos-comprobante/nuevo/")
def crear_tipo_comprobante_nuevo():
    """Crea un tipo de comprobante desde formulario."""
    try:
        tipo_comprobante = crear_item_catalogo_fiscal_desde_formulario(
            "tipos_comprobante",
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "tablas_comunes/tipos_comprobante_form.html",
                page_title="Nuevo tipo de comprobante",
                modo_formulario="alta",
                tipo_comprobante=request.form,
                action_url=url_for("tablas_comunes_fiscales.crear_tipo_comprobante_nuevo"),
                form_titulo="Nuevo tipo de comprobante",
                form_submit_label="Crear tipo",
                form_cancelar_url=url_for(
                    "tablas_comunes_fiscales.ver_listado_tipos_comprobante"
                ),
                codigo_solo_lectura=False,
            ),
            400,
        )

    flash("Tipo de comprobante creado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_comprobante",
            tipo=tipo_comprobante["codigo"],
        )
    )


@bp.get("/tipos-comprobante/<codigo_tipo_comprobante>/editar/")
def ver_formulario_editar_tipo_comprobante(codigo_tipo_comprobante):
    """Muestra formulario de edicion de tipo de comprobante."""
    try:
        contexto = obtener_contexto_detalle_catalogo_fiscal(
            "tipos_comprobante",
            codigo_tipo_comprobante,
            "tipo_comprobante",
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_comprobante"))

    tipo_comprobante = contexto["tipo_comprobante"]
    titulo_formulario = (
        f"Editar tipo de comprobante {tipo_comprobante['codigo']} - "
        f"{tipo_comprobante['descripcion']}"
    )

    return render_template(
        "tablas_comunes/tipos_comprobante_form.html",
        page_title=titulo_formulario,
        modo_formulario="edicion",
        tipo_comprobante=tipo_comprobante,
        action_url=url_for(
            "tablas_comunes_fiscales.actualizar_tipo_comprobante_existente",
            codigo_tipo_comprobante=tipo_comprobante["codigo"],
        ),
        form_titulo=titulo_formulario,
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("tablas_comunes_fiscales.ver_listado_tipos_comprobante"),
        codigo_solo_lectura=True,
    )


@bp.post("/tipos-comprobante/<codigo_tipo_comprobante>/editar/")
def actualizar_tipo_comprobante_existente(codigo_tipo_comprobante):
    """Actualiza un tipo de comprobante desde formulario."""
    try:
        tipo_comprobante = actualizar_item_catalogo_fiscal_desde_formulario(
            "tipos_comprobante",
            codigo_tipo_comprobante,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        tipo_form = {campo: request.form.get(campo, "") for campo in request.form.keys()}
        tipo_form["codigo"] = codigo_tipo_comprobante
        titulo_formulario = (
            f"Editar tipo de comprobante {codigo_tipo_comprobante} - "
            f"{tipo_form.get('descripcion', '')}"
        )
        return (
            render_template(
                "tablas_comunes/tipos_comprobante_form.html",
                page_title=titulo_formulario,
                modo_formulario="edicion",
                tipo_comprobante=tipo_form,
                action_url=url_for(
                    "tablas_comunes_fiscales.actualizar_tipo_comprobante_existente",
                    codigo_tipo_comprobante=codigo_tipo_comprobante,
                ),
                form_titulo=titulo_formulario,
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for(
                    "tablas_comunes_fiscales.ver_listado_tipos_comprobante"
                ),
                codigo_solo_lectura=True,
            ),
            400,
        )

    flash("Tipo de comprobante actualizado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_comprobante",
            tipo=tipo_comprobante["codigo"],
        )
    )


@bp.post("/tipos-comprobante/<codigo_tipo_comprobante>/activar/")
def activar_tipo_comprobante_existente(codigo_tipo_comprobante):
    """Activa un tipo de comprobante sin borrado fisico."""
    try:
        tipo_comprobante = activar_item_catalogo_fiscal(
            "tipos_comprobante",
            codigo_tipo_comprobante,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_comprobante"))

    flash("Tipo de comprobante activado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_comprobante",
            tipo=tipo_comprobante["codigo"],
        )
    )


@bp.post("/tipos-comprobante/<codigo_tipo_comprobante>/desactivar/")
def desactivar_tipo_comprobante_existente(codigo_tipo_comprobante):
    """Desactiva un tipo de comprobante sin borrado fisico."""
    try:
        tipo_comprobante = desactivar_item_catalogo_fiscal(
            "tipos_comprobante",
            codigo_tipo_comprobante,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("tablas_comunes_fiscales.ver_listado_tipos_comprobante"))

    flash("Tipo de comprobante desactivado correctamente.", "success")
    return redirect(
        url_for(
            "tablas_comunes_fiscales.ver_listado_tipos_comprobante",
            tipo=tipo_comprobante["codigo"],
        )
    )
