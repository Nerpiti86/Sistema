from app.tablas_comunes.routes import bp
from app.tablas_comunes import routes_bancos
from app.tablas_comunes.routes_catalogos_fiscales import bp as bp_catalogos_fiscales
from app.tablas_comunes import routes_medios_operativos
from app.tablas_comunes import routes_monedas
from app.tablas_comunes import routes_paises
from app.tablas_comunes import routes_provincias


def register(app):
    app.register_blueprint(bp)
    app.register_blueprint(bp_catalogos_fiscales)
