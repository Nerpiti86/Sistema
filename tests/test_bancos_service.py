from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.bancos_service import (
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
        get_db().execute(
            """
            INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("AAA00", "Banco prueba", 1, 10, "2026-01-01 10:00:00"),
        )
        contexto = obtener_contexto_listado_bancos()

    assert contexto["cantidad_bancos"] == 1
    assert contexto["cantidad_bancos_activos"] == 1
    assert {"bancos", "bancos_activos"}.issubset(contexto)


def test_obtener_contexto_bancos_activos():
    """Valida contexto minimo para selects de bancos activos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            """
            INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?), (?, ?, ?, ?, ?)
            """,
            (
                "AAA00",
                "Banco activo",
                1,
                10,
                "2026-01-01 10:00:00",
                "BBB00",
                "Banco inactivo",
                0,
                20,
                "2026-01-01 10:00:00",
            ),
        )
        contexto = obtener_contexto_bancos_activos()

    codigos = {banco["codigo"] for banco in contexto["bancos"]}

    assert "AAA00" in codigos
    assert "BBB00" not in codigos
    assert contexto["cantidad_bancos"] == len(contexto["bancos"])


def test_obtener_banco_activo_por_codigo_normaliza_codigo():
    """Valida obtencion funcional de banco activo por codigo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            """
            INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("AAA00", "Banco prueba", 1, 10, "2026-01-01 10:00:00"),
        )
        banco = obtener_banco_activo_por_codigo(" aaa00 ")

    assert banco["codigo"] == "AAA00"
    assert banco["descripcion_select"] == "AAA00 - Banco prueba"


def test_obtener_banco_activo_por_codigo_rechaza_inactivo():
    """Valida que el service no devuelva bancos inactivos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            """
            INSERT INTO bancos (codigo, nombre, activo, orden, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("AAA00", "Banco inactivo", 0, 10, "2026-01-01 10:00:00"),
        )

        with pytest.raises(ValueError):
            obtener_banco_activo_por_codigo("AAA00")


def test_normalizar_codigo_banco_desde_formulario():
    """Valida normalizacion de codigo recibido desde formulario."""
    assert normalizar_codigo_banco_desde_formulario(" aaa00 ") == "AAA00"


def test_normalizar_codigo_banco_desde_formulario_rechaza_vacio():
    """Valida rechazo de codigo vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_codigo_banco_desde_formulario("")
