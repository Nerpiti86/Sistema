from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.monedas_service import (
    normalizar_codigo_moneda_desde_formulario,
    obtener_contexto_listado_monedas,
    obtener_contexto_monedas_activas,
    obtener_moneda_activa_por_codigo,
)


def test_monedas_service_no_usa_sql_directo():
    """Valida que el service de monedas no ejecute SQL ni use get_db."""
    contenido = Path("app/shared/monedas_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_obtener_contexto_listado_monedas():
    """Valida contexto completo del maestro monedas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        contexto = obtener_contexto_listado_monedas()

    assert contexto["cantidad_monedas"] >= 3
    assert contexto["cantidad_monedas_activas"] >= 3
    assert {"monedas", "monedas_activas"}.issubset(contexto)


def test_obtener_contexto_monedas_activas():
    """Valida contexto minimo para selects de monedas activas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            "UPDATE monedas SET activa = 0 WHERE codigo = ?",
            ("EUR",),
        )

        contexto = obtener_contexto_monedas_activas()

    codigos = {moneda["codigo"] for moneda in contexto["monedas"]}

    assert "ARS" in codigos
    assert "USD" in codigos
    assert "EUR" not in codigos
    assert contexto["cantidad_monedas"] == len(contexto["monedas"])


def test_obtener_moneda_activa_por_codigo_normaliza_codigo():
    """Valida obtencion funcional de moneda activa por codigo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        moneda = obtener_moneda_activa_por_codigo("ars")

    assert moneda["codigo"] == "ARS"
    assert moneda["simbolo"] == "$"


def test_obtener_moneda_activa_por_codigo_rechaza_inactiva():
    """Valida que el service no devuelva monedas inactivas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            "UPDATE monedas SET activa = 0 WHERE codigo = ?",
            ("USD",),
        )

        with pytest.raises(ValueError):
            obtener_moneda_activa_por_codigo("USD")


def test_normalizar_codigo_moneda_desde_formulario():
    """Valida normalizacion de codigo recibido desde formulario."""
    assert normalizar_codigo_moneda_desde_formulario(" usd ") == "USD"


def test_normalizar_codigo_moneda_desde_formulario_rechaza_vacio():
    """Valida rechazo de codigo vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_codigo_moneda_desde_formulario("")
