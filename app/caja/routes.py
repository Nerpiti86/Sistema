from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.caja.movimientos_caja_service import (
    confirmar_movimiento_caja_desde_formulario,
    obtener_contexto_detalle_movimiento_caja,
    obtener_contexto_formulario_movimiento_caja,
    obtener_contexto_listado_movimientos_caja,
)

bp = Blueprint(
    "caja",
    __name__,
    url_prefix="/caja",
    template_folder="templates",
)


@bp.get("/movimientos/")
def ver_listado_movimientos_caja():
    """Muestra listado de movimientos de caja en solo lectura."""
    contexto = obtener_contexto_listado_movimientos_caja()

    return render_template(
        "caja/movimientos_caja.html",
        page_title="Movimientos de caja",
        **contexto,
    )


@bp.get("/movimientos/<int:movimiento_id>/")
def ver_detalle_movimiento_caja(movimiento_id):
    """Muestra detalle de movimiento de caja en solo lectura."""
    try:
        contexto = obtener_contexto_detalle_movimiento_caja(movimiento_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("caja.ver_listado_movimientos_caja"))

    movimiento = contexto["movimiento_caja"]

    return render_template(
        "caja/movimientos_caja_detalle.html",
        page_title=f"Movimiento de caja {movimiento['id']}",
        **contexto,
    )


@bp.get("/movimientos/nuevo/")
def ver_formulario_nuevo_movimiento_caja():
    """Muestra pantalla transversal de movimiento de caja."""
    try:
        contexto = obtener_contexto_formulario_movimiento_caja(request.args)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("ui.dashboard"))

    return render_template(
        "caja/movimientos_caja_form.html",
        page_title="Nuevo movimiento de caja",
        action_url=url_for("caja.confirmar_movimiento_caja"),
        **contexto,
    )


@bp.post("/movimientos/nuevo/")
def confirmar_movimiento_caja():
    """Confirma un movimiento de caja desde una intencion pendiente."""
    try:
        resultado = confirmar_movimiento_caja_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        try:
            contexto = obtener_contexto_formulario_movimiento_caja(request.form)
        except ValueError as exc_contexto:
            flash(str(exc_contexto), "danger")
            return redirect(url_for("ui.dashboard"))

        return (
            render_template(
                "caja/movimientos_caja_form.html",
                page_title="Nuevo movimiento de caja",
                action_url=url_for("caja.confirmar_movimiento_caja"),
                **contexto,
            ),
            400,
        )

    flash("Movimiento de caja confirmado correctamente.", "success")

    if resultado["origen_tipo"] == "RECIBO_CLIENTE":
        return redirect(
            url_for(
                "gestion.ver_cuenta_corriente_cliente",
                cliente_id=resultado["cliente_id"],
                cobranza=resultado["cobranza_id"],
            )
        )

    return redirect(url_for("ui.dashboard"))
