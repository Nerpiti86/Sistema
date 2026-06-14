from app.tablas_comunes.routes import bp
from app.tablas_comunes.routes_catalogos_fiscales import bp as bp_catalogos_fiscales


def register(app):
    app.register_blueprint(bp)
    app.register_blueprint(bp_catalogos_fiscales)
