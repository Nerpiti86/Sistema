from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.contabilidad.ejercicios_contables_service import (
    crear_ejercicio_contable_desde_formulario,
    obtener_contexto_listado_ejercicios_contables,
)

bp = Blueprint(
    "contabilidad",
    __name__,
    url_prefix="/contabilidad",
    template_folder="templates",
)


@bp.get("/")
def index():
    return render_template(
        "contabilidad/index.html",
        page_title="Contabilidad",
    )


@bp.get("/ejercicios-contables/")
def ver_listado_ejercicios_contables():
    contexto_ejercicios_contables = obtener_contexto_listado_ejercicios_contables()

    return render_template(
        "contabilidad/ejercicios_contables.html",
        page_title="Ejercicios contables",
        **contexto_ejercicios_contables,
    )

@bp.post("/ejercicios-contables/nuevo/")
def crear_ejercicio_contable():
    """
    Crea un ejercicio contable desde POST y vuelve al listado.

    Esta route no ejecuta SQL directo. La normalizacion queda en service y la
    persistencia queda en repository.
    """
    try:
        crear_ejercicio_contable_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.ver_listado_ejercicios_contables"))

    flash("Ejercicio contable creado correctamente.", "success")
    return redirect(url_for("contabilidad.ver_listado_ejercicios_contables"))
