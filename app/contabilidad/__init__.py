from app.contabilidad.routes import bp
from app.contabilidad import routes_asientos
from app.contabilidad import routes_cuentas
from app.contabilidad import routes_ejercicios
from app.contabilidad import routes_indices
from app.contabilidad import routes_libros


def register(app):
    app.register_blueprint(bp)
