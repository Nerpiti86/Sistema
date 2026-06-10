from app.tablas_comunes.routes import bp


def register(app):
    app.register_blueprint(bp)
