from pathlib import Path

from flask import Flask

from app.config import Config
from app.db import init_app as init_db_app
from app.errors import register_error_handlers
from app.modules import register_modules


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    init_db_app(app)
    register_error_handlers(app)
    register_modules(app)

    return app
