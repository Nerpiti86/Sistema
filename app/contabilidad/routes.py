from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.contabilidad.ejercicios_contables_service import (
    crear_ejercicio_contable_desde_formulario,
    obtener_contexto_detalle_ejercicio_contable,
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


@bp.get("/ejercicios-contables/nuevo/")
def ver_formulario_crear_ejercicio_contable():
    """
    Muestra formulario de alta de ejercicios_contables.

    Esta route no ejecuta SQL directo. Solo prepara contexto visual minimo
    para el template de alta.
    """
    return render_template(
        "contabilidad/ejercicios_contables_form.html",
        page_title="Crear ejercicio contable",
        ejercicio_contable_form={
            "codigo": "",
            "nombre": "",
            "fecha_desde": "",
            "fecha_hasta": "",
            "estado": "ABIERTO",
            "fase_cierre": "ABIERTO",
            "activo": False,
            "bloqueado": False,
            "es_primer_ejercicio": False,
            "observaciones_cierre": "",
        },
        estados_ejercicio_contable=("ABIERTO", "CERRADO"),
        fases_cierre_ejercicio_contable=("ABIERTO", "EN_CIERRE", "BLOQUEADO"),
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

@bp.get("/ejercicios-contables/<codigo>/")
def ver_detalle_ejercicio_contable(codigo):
    """
    Muestra detalle de un ejercicio contable.

    Esta route no ejecuta SQL directo. Pide contexto al service y renderiza una
    pantalla de solo lectura.
    """
    try:
        contexto_detalle = obtener_contexto_detalle_ejercicio_contable(codigo)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.ver_listado_ejercicios_contables"))

    ejercicio_contable = contexto_detalle["ejercicio_contable"]

    return render_template(
        "contabilidad/ejercicios_contables_detalle.html",
        page_title=f"Ejercicio contable {ejercicio_contable['codigo']}",
        **contexto_detalle,
    )
