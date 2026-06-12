from flask import Blueprint, redirect, render_template, url_for

from app.shared.bancos_service import obtener_contexto_listado_bancos
from app.shared.monedas_service import obtener_contexto_listado_monedas

bp = Blueprint(
    "tablas_comunes",
    __name__,
    url_prefix="/tablas-comunes",
    template_folder="templates",
)


@bp.get("/")
def index():
    """Redirige al primer maestro de tablas comunes."""
    return redirect(url_for("tablas_comunes.ver_listado_monedas"))


@bp.get("/monedas/")
def ver_listado_monedas():
    """
    Muestra listado del maestro transversal de monedas.

    Esta route no ejecuta SQL directo. El contexto de pantalla queda delegado
    al service transversal de monedas.
    """
    contexto_monedas = obtener_contexto_listado_monedas()

    return render_template(
        "tablas_comunes/monedas.html",
        page_title="Monedas",
        **contexto_monedas,
    )


@bp.get("/bancos/")
def ver_listado_bancos():
    """
    Muestra listado del maestro transversal de bancos.

    Esta route no ejecuta SQL directo. El contexto de pantalla queda delegado
    al service transversal de bancos.
    """
    contexto_bancos = obtener_contexto_listado_bancos()

    return render_template(
        "tablas_comunes/bancos.html",
        page_title="Bancos",
        **contexto_bancos,
    )
