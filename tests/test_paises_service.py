from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.gestion.paises_repository import crear_pais
from app.gestion.paises_service import (
    activar_pais,
    actualizar_pais_desde_formulario,
    crear_pais_desde_formulario,
    desactivar_pais,
    normalizar_id_pais_desde_formulario,
    obtener_contexto_detalle_pais,
    obtener_contexto_listado_paises,
    obtener_contexto_paises_activos,
    obtener_pais_activo_por_id,
)


def test_paises_service_no_usa_sql_directo():
    """Valida que el service de paises no ejecute SQL ni use get_db."""
    contenido = Path("app/gestion/paises_service.py").read_text(encoding="utf-8")

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_obtener_contexto_listado_paises():
    """Valida contexto completo del maestro paises."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})
        crear_pais({"nombre": "Inactivo", "codigo_iso": None, "activo": 0, "orden": 20})

        contexto = obtener_contexto_listado_paises()

    assert contexto["cantidad_paises"] == 2
    assert contexto["cantidad_paises_activos"] == 1
    assert {"paises", "paises_activos"}.issubset(contexto)


def test_obtener_contexto_paises_activos():
    """Valida contexto minimo para selects de gestion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})
        crear_pais({"nombre": "Inactivo", "codigo_iso": None, "activo": 0, "orden": 20})

        contexto = obtener_contexto_paises_activos()

    nombres = {pais["nombre"] for pais in contexto["paises"]}

    assert "Argentina" in nombres
    assert "Inactivo" not in nombres
    assert contexto["cantidad_paises"] == len(contexto["paises"])


def test_obtener_contexto_detalle_pais():
    """Valida contexto de detalle para edicion de pais."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})

        contexto = obtener_contexto_detalle_pais(str(pais["id"]))

    assert contexto["pais"]["id"] == pais["id"]
    assert contexto["pais"]["nombre"] == "Argentina"


def test_obtener_contexto_detalle_pais_rechaza_inexistente():
    """Valida rechazo de detalle para pais inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            obtener_contexto_detalle_pais(999)


def test_obtener_pais_activo_por_id():
    """Valida obtencion funcional de pais activo por id."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})

        pais_activo = obtener_pais_activo_por_id(str(pais["id"]))

    assert pais_activo["id"] == pais["id"]
    assert pais_activo["esta_activo"] is True


def test_obtener_pais_activo_por_id_rechaza_inactivo():
    """Valida que el service no devuelva paises inactivos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais({"nombre": "Inactivo", "codigo_iso": None, "activo": 0, "orden": 10})

        with pytest.raises(ValueError):
            obtener_pais_activo_por_id(pais["id"])


def test_crear_pais_desde_formulario():
    """Valida alta manual de pais desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais_desde_formulario(
            {
                "nombre": "  Argentina  ",
                "codigo_iso": " ar ",
                "activo": "1",
                "orden": "30",
            }
        )

    assert pais["nombre"] == "Argentina"
    assert pais["codigo_iso"] == "AR"
    assert pais["activo"] == 1
    assert pais["orden"] == 30


def test_crear_pais_desde_formulario_checkbox_ausente_inactiva():
    """Valida contrato HTML: checkbox ausente equivale a 0."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais_desde_formulario(
            {
                "nombre": "Inactivo",
                "codigo_iso": "",
                "orden": "10",
            }
        )

    assert pais["activo"] == 0
    assert pais["esta_activo"] is False


def test_actualizar_pais_desde_formulario():
    """Valida edicion manual de pais desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})

        pais_actualizado = actualizar_pais_desde_formulario(
            pais["id"],
            {
                "nombre": "Argentina editado",
                "codigo_iso": "ARG",
                "activo": "1",
                "orden": "15",
            },
        )

    assert pais_actualizado["id"] == pais["id"]
    assert pais_actualizado["nombre"] == "Argentina editado"
    assert pais_actualizado["codigo_iso"] == "ARG"
    assert pais_actualizado["orden"] == 15


def test_activar_desactivar_pais():
    """Valida baja logica por activar/desactivar desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})

        pais_desactivado = desactivar_pais(pais["id"])
        pais_activado = activar_pais(pais["id"])

    assert pais_desactivado["activo"] == 0
    assert pais_desactivado["esta_activo"] is False
    assert pais_activado["activo"] == 1
    assert pais_activado["esta_activo"] is True


def test_normalizar_id_pais_desde_formulario():
    """Valida normalizacion de id recibido desde formulario."""
    assert normalizar_id_pais_desde_formulario(" 12 ") == 12


def test_normalizar_id_pais_desde_formulario_rechaza_vacio():
    """Valida rechazo de id vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_id_pais_desde_formulario("")


def test_normalizar_id_pais_desde_formulario_rechaza_no_numerico():
    """Valida rechazo de id no numerico desde formulario."""
    with pytest.raises(ValueError):
        normalizar_id_pais_desde_formulario("abc")
