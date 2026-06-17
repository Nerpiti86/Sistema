from flask import Blueprint, render_template, request

from app.caja.movimientos_caja_service import (
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
    """Muestra pantalla WIP de movimiento de caja."""
    contexto = obtener_contexto_formulario_movimiento_caja(request.args)

    return render_template(
        "caja/movimientos_caja_form.html",
        page_title="Nuevo movimiento de caja",
        **contexto,
    )
