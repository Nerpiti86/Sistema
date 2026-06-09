import sqlite3
from pathlib import Path

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        database = current_app.config["DATABASE"]

        if database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        if database != ":memory:":
            connection.execute("PRAGMA journal_mode = WAL")

        g.db = connection

    return g.db


def close_db(error=None):
    connection = g.pop("db", None)

    if connection is not None:
        connection.close()


def apply_migrations():
    db = get_db()
    migrations_path = Path(current_app.root_path).parent / "migrations"

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    applied = {
        row["filename"]
        for row in db.execute("SELECT filename FROM schema_migrations")
    }

    for migration in sorted(migrations_path.glob("*.sql")):
        if migration.name in applied:
            continue

        sql = migration.read_text(encoding="utf-8")

        with db:
            db.executescript(sql)
            db.execute(
                "INSERT INTO schema_migrations (filename) VALUES (?)",
                (migration.name,),
            )


def init_app(app):
    app.teardown_appcontext(close_db)

    @app.cli.command("db-migrate")
    def db_migrate_command():
        apply_migrations()
        click.echo("Migraciones aplicadas correctamente.")
