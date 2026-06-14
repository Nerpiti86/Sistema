from flask import render_template

from app.contabilidad.blueprint import bp


@bp.get("/")
def index():
    return render_template(
        "contabilidad/index.html",
        page_title="Contabilidad",
    )
