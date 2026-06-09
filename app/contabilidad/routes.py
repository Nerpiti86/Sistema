from flask import Blueprint, render_template

from app.contabilidad.ejercicios_contables_service import (
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
