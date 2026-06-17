from app.caja.routes import bp


def register(app):
    app.register_blueprint(bp)
