from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_dashboard_responde_ok():
    """Valida que la app base levante y responda el dashboard inicial."""
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"NeriSoft Sistema" in response.data


def test_migraciones_aplican_schema_inicial():
    """Valida que el esquema inicial cree app_settings y registre version."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        row = get_db().execute(
            "SELECT valor FROM app_settings WHERE clave = ?",
            ("schema_version",),
        ).fetchone()

    assert row is not None
    assert row["valor"] == "001"
