from flask import Blueprint, render_template

bp = Blueprint("ui", __name__, template_folder="templates")


@bp.get("/")
def dashboard():
    return render_template("dashboard.html", page_title="Inicio")
