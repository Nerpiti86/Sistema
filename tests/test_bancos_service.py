from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.bancos_service import (
    activar_banco,
    actualizar_banco_desde_formulario,
    crear_banco_desde_formulario,
    desactivar_banco,
    normalizar_codigo_banco_desde_formulario,
    obtener_banco_activo_por_codigo,
    obtener_contexto_bancos_activos,
    obtener_contexto_listado_bancos,
)


def test_bancos_service_no_usa_sql_directo():
    """Valida que el service de bancos no ejecute SQL ni use get_db."""
    contenido = Path("app/shared/bancos_service.py").read_text(encoding="utf-8")

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_obtener_contexto_listado_bancos():
    """Valida contexto completo del maestro bancos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        contexto = obtener_contexto_listado_bancos()

    assert contexto["cantidad_bancos"] == 73
    assert contexto["cantidad_bancos_activos"] == 73
    assert {"bancos", "bancos_activos"}.issubset(contexto)


def test_obtener_contexto_bancos_activos():
    """Valida contexto minimo para selects de bancos activos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            "UPDATE bancos SET activo = 0 WHERE codigo = ?",
            ("285",),
        )
        contexto = obtener_contexto_bancos_activos()

    codigos = {banco["codigo"] for banco in contexto["bancos"]}

    assert "7" in codigos
    assert "285" not in codigos
    assert contexto["cantidad_bancos"] == len(contexto["bancos"])


def test_obtener_banco_activo_por_codigo_normaliza_codigo():
    """Valida obtencion funcional de banco activo por codigo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        banco = obtener_banco_activo_por_codigo(" 285 ")

    assert banco["codigo"] == "285"
    assert banco["descripcion_select"] == "285 - BANCO MACRO S.A."


def test_obtener_banco_activo_por_codigo_rechaza_inactivo():
    """Valida que el service no devuelva bancos inactivos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            "UPDATE bancos SET activo = 0 WHERE codigo = ?",
            ("285",),
        )

        with pytest.raises(ValueError):
            obtener_banco_activo_por_codigo("285")


def test_crear_banco_desde_formulario():
    """Valida alta manual de banco desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        banco = crear_banco_desde_formulario(
            {
                "codigo": "99999",
                "nombre": "Banco manual prueba",
                "activo": "1",
                "orden": "999",
            }
        )

    assert banco["codigo"] == "99999"
    assert banco["nombre"] == "BANCO MANUAL PRUEBA"
    assert banco["activo"] == 1
    assert banco["orden"] == 999


def test_actualizar_banco_desde_formulario():
    """Valida edicion manual de banco desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        banco = actualizar_banco_desde_formulario(
            "285",
            {
                "nombre": "Banco macro editado",
                "activo": "1",
                "orden": "333",
            },
        )

    assert banco["codigo"] == "285"
    assert banco["nombre"] == "BANCO MACRO EDITADO"
    assert banco["orden"] == 333


def test_activar_desactivar_banco():
    """Valida baja logica por activar/desactivar sin borrado fisico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        banco_desactivado = desactivar_banco("285")
        banco_activado = activar_banco("285")

    assert banco_desactivado["activo"] == 0
    assert banco_desactivado["esta_activo"] is False
    assert banco_activado["activo"] == 1
    assert banco_activado["esta_activo"] is True


def test_normalizar_codigo_banco_desde_formulario():
    """Valida normalizacion de codigo recibido desde formulario."""
    assert normalizar_codigo_banco_desde_formulario(" 285 ") == "285"


def test_normalizar_codigo_banco_desde_formulario_rechaza_vacio():
    """Valida rechazo de codigo vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_codigo_banco_desde_formulario("")
