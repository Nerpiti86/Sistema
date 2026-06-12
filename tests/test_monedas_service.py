from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.monedas_service import (
    activar_moneda,
    actualizar_moneda_desde_formulario,
    crear_moneda_desde_formulario,
    desactivar_moneda,
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


def test_crear_moneda_desde_formulario():
    """Valida alta manual de moneda desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        moneda = crear_moneda_desde_formulario(
            {
                "codigo": "uyu",
                "nombre": "Peso uruguayo",
                "simbolo": "$U",
                "decimales": "2",
                "activa": "1",
                "orden": "40",
            }
        )

    assert moneda["codigo"] == "UYU"
    assert moneda["nombre"] == "Peso uruguayo"
    assert moneda["simbolo"] == "$U"
    assert moneda["activa"] == 1


def test_actualizar_moneda_desde_formulario():
    """Valida edicion manual de moneda desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        moneda = actualizar_moneda_desde_formulario(
            "USD",
            {
                "nombre": "Dolar estadounidense editado",
                "simbolo": "USD",
                "decimales": "2",
                "activa": "1",
                "orden": "25",
            },
        )

    assert moneda["codigo"] == "USD"
    assert moneda["nombre"] == "Dolar estadounidense editado"
    assert moneda["simbolo"] == "USD"
    assert moneda["orden"] == 25


def test_activar_desactivar_moneda():
    """Valida baja logica por activar/desactivar sin borrado fisico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        moneda_desactivada = desactivar_moneda("USD")
        moneda_activada = activar_moneda("USD")

    assert moneda_desactivada["activa"] == 0
    assert moneda_desactivada["esta_activa"] is False
    assert moneda_activada["activa"] == 1
    assert moneda_activada["esta_activa"] is True


def test_normalizar_codigo_moneda_desde_formulario():
    """Valida normalizacion de codigo recibido desde formulario."""
    assert normalizar_codigo_moneda_desde_formulario(" usd ") == "USD"


def test_normalizar_codigo_moneda_desde_formulario_rechaza_vacio():
    """Valida rechazo de codigo vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_codigo_moneda_desde_formulario("")
