from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.caja.movimientos_caja_service import (
    confirmar_movimiento_caja_desde_formulario,
    obtener_contexto_formulario_movimiento_caja,
)

bp = Blueprint(
    "caja",
    __name__,
    url_prefix="/caja",
    template_folder="templates",
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
