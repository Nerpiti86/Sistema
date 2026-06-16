from flask import flash, redirect, render_template, request, url_for

from app.contabilidad.blueprint import bp
from app.contabilidad.libros_contables_service import (
    obtener_contexto_pantalla_libro_diario,
)


@bp.get("/libros/diario/")
def ver_libro_diario():
    """
    Muestra el Libro Diario.

    Esta route no ejecuta SQL directo. El contexto queda preparado por el
    service de libros contables.
    """
    try:
        contexto_libro_diario = obtener_contexto_pantalla_libro_diario(request.args)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.index"))

    return render_template(
        "contabilidad/libro_diario.html",
        page_title="Libro diario",
        **contexto_libro_diario,
    )
