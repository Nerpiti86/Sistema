from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app.gestion.articulos_venta_service import (
    activar_articulo_venta,
    actualizar_articulo_venta_desde_formulario,
    crear_articulo_venta_desde_formulario,
    desactivar_articulo_venta,
    obtener_contexto_edicion_articulo_venta,
    obtener_contexto_formulario_articulo_venta,
    obtener_contexto_listado_articulos_venta,
    obtener_lookup_articulos_venta_activos,
)
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
from app.gestion.ventas_comprobantes_service import (
    confirmar_comprobante_venta,
    crear_y_confirmar_comprobante_venta_desde_formulario,
    obtener_contexto_detalle_comprobante_venta,
    obtener_contexto_formulario_comprobante_venta,
    obtener_contexto_listado_comprobantes_venta,
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



@bp.get("/ventas/comprobantes/")
def ver_listado_comprobantes_venta():
    """Muestra listado de comprobantes de venta."""
    contexto = obtener_contexto_listado_comprobantes_venta()

    return render_template(
        "gestion/ventas_comprobantes.html",
        page_title="Comprobantes de venta",
        **contexto,
    )



@bp.get("/ventas/comprobantes/nuevo/")
def ver_formulario_nuevo_comprobante_venta():
    """Muestra formulario minimo de alta de comprobante de venta."""
    contexto = obtener_contexto_formulario_comprobante_venta()

    return render_template(
        "gestion/ventas_comprobantes_form.html",
        page_title="Nuevo comprobante de venta",
        action_url=url_for("gestion.crear_comprobante_venta_nuevo"),
        form_cancelar_url=url_for("gestion.ver_listado_comprobantes_venta"),
        **contexto,
    )


@bp.post("/ventas/comprobantes/nuevo/")
def crear_comprobante_venta_nuevo():
    """Crea y confirma un comprobante de venta desde formulario."""
    try:
        resultado_confirmacion = crear_y_confirmar_comprobante_venta_desde_formulario(request.form)
        comprobante = resultado_confirmacion["comprobante"]
    except ValueError as exc:
        flash(str(exc), "danger")
        contexto = obtener_contexto_formulario_comprobante_venta(
            _normalizar_formulario_para_template(request.form)
        )
        return (
            render_template(
                "gestion/ventas_comprobantes_form.html",
                page_title="Nuevo comprobante de venta",
                action_url=url_for("gestion.crear_comprobante_venta_nuevo"),
                form_cancelar_url=url_for("gestion.ver_listado_comprobantes_venta"),
                **contexto,
            ),
            400,
        )

    flash("Comprobante de venta confirmado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_detalle_comprobante_venta",
            comprobante_id=comprobante["id"],
        )
    )


@bp.get("/ventas/comprobantes/<int:comprobante_id>/")
def ver_detalle_comprobante_venta(comprobante_id):
    """Muestra detalle de un comprobante de venta."""
    try:
        contexto = obtener_contexto_detalle_comprobante_venta(comprobante_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_comprobantes_venta"))

    comprobante = contexto["comprobante_venta"]

    return render_template(
        "gestion/ventas_comprobantes_detalle.html",
        page_title=f"Comprobante de venta {comprobante['numero_formateado']}",
        **contexto,
    )


@bp.post("/ventas/comprobantes/<int:comprobante_id>/confirmar/")
def confirmar_comprobante_venta_existente(comprobante_id):
    """Confirma un comprobante de venta sin mover fondos."""
    try:
        resultado = confirmar_comprobante_venta(comprobante_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(
            url_for(
                "gestion.ver_detalle_comprobante_venta",
                comprobante_id=comprobante_id,
            )
        )

    comprobante = resultado["comprobante"]
    flash("Comprobante de venta confirmado correctamente.", "success")

    return redirect(
        url_for(
            "gestion.ver_detalle_comprobante_venta",
            comprobante_id=comprobante["id"],
        )
    )


@bp.get("/productos-servicios-venta/")
def ver_listado_productos_servicios_venta():
    """Muestra listado del maestro de productos o servicios para la venta."""
    contexto = obtener_contexto_listado_articulos_venta()

    return render_template(
        "gestion/productos_servicios_venta.html",
        page_title="Productos o servicios para la venta",
        **contexto,
    )


@bp.get("/productos-servicios-venta/nuevo/")
def ver_formulario_nuevo_producto_servicio_venta():
    """Muestra formulario de alta de producto o servicio para la venta."""
    contexto_formulario = obtener_contexto_formulario_articulo_venta()

    return render_template(
        "gestion/productos_servicios_venta_form.html",
        page_title="Nuevo producto o servicio para la venta",
        modo_formulario="alta",
        action_url=url_for("gestion.crear_producto_servicio_venta_nuevo"),
        form_titulo="Nuevo producto o servicio para la venta",
        form_submit_label="Crear producto o servicio",
        form_cancelar_url=url_for("gestion.ver_listado_productos_servicios_venta"),
        **contexto_formulario,
    )


@bp.post("/productos-servicios-venta/nuevo/")
def crear_producto_servicio_venta_nuevo():
    """Crea un producto o servicio para la venta desde formulario."""
    try:
        articulo = crear_articulo_venta_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        contexto_formulario = obtener_contexto_formulario_articulo_venta(
            _normalizar_formulario_para_template(request.form)
        )
        return (
            render_template(
                "gestion/productos_servicios_venta_form.html",
                page_title="Nuevo producto o servicio para la venta",
                modo_formulario="alta",
                action_url=url_for("gestion.crear_producto_servicio_venta_nuevo"),
                form_titulo="Nuevo producto o servicio para la venta",
                form_submit_label="Crear producto o servicio",
                form_cancelar_url=url_for("gestion.ver_listado_productos_servicios_venta"),
                **contexto_formulario,
            ),
            400,
        )

    flash("Producto o servicio para la venta creado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_listado_productos_servicios_venta",
            articulo=articulo["id"],
        )
    )


@bp.get("/productos-servicios-venta/buscar/")
def buscar_productos_servicios_venta_json():
    """Devuelve productos o servicios activos para lookup de comprobantes."""
    termino_busqueda = request.args.get("q", "")
    limite = request.args.get("limite", 10)

    try:
        lookup_articulos = obtener_lookup_articulos_venta_activos(
            termino_busqueda,
            limite,
        )
    except ValueError as exc:
        return (
            jsonify(
                {
                    "q": str(termino_busqueda or "").strip(),
                    "cantidad": 0,
                    "resultados": [],
                    "mensaje": str(exc),
                }
            ),
            400,
        )

    return jsonify(lookup_articulos)


@bp.get("/productos-servicios-venta/<int:articulo_venta_id>/editar/")
def ver_formulario_editar_producto_servicio_venta(articulo_venta_id):
    """Muestra formulario de edicion de producto o servicio para la venta."""
    try:
        contexto_formulario = obtener_contexto_edicion_articulo_venta(
            articulo_venta_id
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_productos_servicios_venta"))

    articulo = contexto_formulario["articulo"]

    return render_template(
        "gestion/productos_servicios_venta_form.html",
        page_title=f"Editar producto o servicio para la venta {articulo['nombre']}",
        modo_formulario="edicion",
        action_url=url_for(
            "gestion.actualizar_producto_servicio_venta_existente",
            articulo_venta_id=articulo["id"],
        ),
        form_titulo=f"Editar producto o servicio para la venta {articulo['nombre']}",
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for("gestion.ver_listado_productos_servicios_venta"),
        **contexto_formulario,
    )


@bp.post("/productos-servicios-venta/<int:articulo_venta_id>/editar/")
def actualizar_producto_servicio_venta_existente(articulo_venta_id):
    """Actualiza un producto o servicio para la venta desde formulario."""
    try:
        articulo = actualizar_articulo_venta_desde_formulario(
            articulo_venta_id,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        articulo_form = _normalizar_formulario_para_template(request.form)
        articulo_form["id"] = articulo_venta_id
        contexto_formulario = obtener_contexto_formulario_articulo_venta(
            articulo_form
        )

        return (
            render_template(
                "gestion/productos_servicios_venta_form.html",
                page_title=f"Editar producto o servicio para la venta {articulo_venta_id}",
                modo_formulario="edicion",
                action_url=url_for(
                    "gestion.actualizar_producto_servicio_venta_existente",
                    articulo_venta_id=articulo_venta_id,
                ),
                form_titulo=f"Editar producto o servicio para la venta {articulo_venta_id}",
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for("gestion.ver_listado_productos_servicios_venta"),
                **contexto_formulario,
            ),
            400,
        )

    flash("Producto o servicio para la venta actualizado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_listado_productos_servicios_venta",
            articulo=articulo["id"],
        )
    )


@bp.post("/productos-servicios-venta/<int:articulo_venta_id>/activar/")
def activar_producto_servicio_venta_existente(articulo_venta_id):
    """Activa un producto o servicio para la venta sin borrado fisico."""
    try:
        articulo = activar_articulo_venta(articulo_venta_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_productos_servicios_venta"))

    flash("Producto o servicio para la venta activado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_listado_productos_servicios_venta",
            articulo=articulo["id"],
        )
    )


@bp.post("/productos-servicios-venta/<int:articulo_venta_id>/desactivar/")
def desactivar_producto_servicio_venta_existente(articulo_venta_id):
    """Desactiva un producto o servicio para la venta sin borrado fisico."""
    try:
        articulo = desactivar_articulo_venta(articulo_venta_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("gestion.ver_listado_productos_servicios_venta"))

    flash("Producto o servicio para la venta desactivado correctamente.", "success")
    return redirect(
        url_for(
            "gestion.ver_listado_productos_servicios_venta",
            articulo=articulo["id"],
        )
    )


def _normalizar_formulario_para_template(formulario) -> dict[str, str]:
    """Convierte request.form en dict simple para re-render de errores."""
    return {campo: formulario.get(campo, "") for campo in formulario.keys()}
