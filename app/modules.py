from app.contabilidad import register as register_contabilidad
from app.tablas_comunes import register as register_tablas_comunes
from app.ui import register as register_ui


def register_modules(app):
    register_ui(app)
    register_tablas_comunes(app)
    register_contabilidad(app)
