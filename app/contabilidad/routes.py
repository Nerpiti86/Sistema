from flask import Blueprint, render_template

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
