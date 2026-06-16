from flask import flash, redirect, render_template, request, url_for

from app.contabilidad.blueprint import bp
from app.contabilidad.libros_contables_service import (
    obtener_contexto_pantalla_libro_diario,
    obtener_contexto_pantalla_mayor_general,
    obtener_contexto_pantalla_mayor_por_cuenta,
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



@bp.get("/libros/mayor-general/")
def ver_mayor_general():
    """
    Muestra el Libro Mayor General.

    Esta route no ejecuta SQL directo. El contexto queda preparado por el
    service de libros contables.
    """
    try:
        contexto_mayor_general = obtener_contexto_pantalla_mayor_general(
            request.args
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.index"))

    return render_template(
        "contabilidad/mayor_general.html",
        page_title="Libro mayor general",
        **contexto_mayor_general,
    )


@bp.get("/libros/mayor-cuenta/")
def ver_mayor_por_cuenta():
    """
    Muestra el Libro Mayor por Cuenta.

    Esta route no ejecuta SQL directo. El contexto queda preparado por el
    service de libros contables.
    """
    try:
        contexto_mayor_cuenta = obtener_contexto_pantalla_mayor_por_cuenta(
            request.args
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.index"))

    return render_template(
        "contabilidad/mayor_cuenta.html",
        page_title="Libro mayor por cuenta",
        **contexto_mayor_cuenta,
    )
