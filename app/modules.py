from app.contabilidad import register as register_contabilidad
from app.ui import register as register_ui


def register_modules(app):
    register_ui(app)
    register_contabilidad(app)
