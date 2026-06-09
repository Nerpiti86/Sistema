import os
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    DATABASE = os.environ.get(
        "DATABASE",
        str(BASE_DIR / "instance" / "sistema.sqlite3"),
    )


class TestConfig(Config):
    TESTING = True
    DATABASE = ":memory:"
