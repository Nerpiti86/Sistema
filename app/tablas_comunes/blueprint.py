from flask import Blueprint


bp = Blueprint(
    "tablas_comunes",
    __name__,
    url_prefix="/tablas-comunes",
    template_folder="templates",
)
