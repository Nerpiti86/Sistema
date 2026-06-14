from flask import redirect, url_for

from app.tablas_comunes.blueprint import bp


@bp.get("/")
def index():
    """Redirige al primer maestro de tablas comunes."""
    return redirect(url_for("tablas_comunes.ver_listado_monedas"))
