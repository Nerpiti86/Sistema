from app.contabilidad.routes import bp


def register(app):
    app.register_blueprint(bp)
