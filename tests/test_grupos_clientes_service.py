from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.gestion.grupos_clientes_repository import crear_grupo_cliente
from app.gestion.grupos_clientes_service import (
    activar_grupo_cliente,
    actualizar_grupo_cliente_desde_formulario,
    crear_grupo_cliente_desde_formulario,
    desactivar_grupo_cliente,
    normalizar_id_grupo_cliente_desde_formulario,
    obtener_contexto_detalle_grupo_cliente,
    obtener_contexto_grupos_clientes_activos,
    obtener_contexto_listado_grupos_clientes,
    obtener_grupo_cliente_activo_por_id,
)


def test_grupos_clientes_service_no_usa_sql_directo():
    """Valida que el service de grupos de clientes no ejecute SQL ni use get_db."""
    contenido = Path("app/gestion/grupos_clientes_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_obtener_contexto_listado_grupos_clientes():
    """Valida contexto completo del maestro grupos de clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})
        crear_grupo_cliente({"nombre": "Inactivo", "activo": 0, "orden": 20})

        contexto = obtener_contexto_listado_grupos_clientes()

    assert contexto["cantidad_grupos_clientes"] == 2
    assert contexto["cantidad_grupos_clientes_activos"] == 1
    assert {"grupos_clientes", "grupos_clientes_activos"}.issubset(contexto)


def test_obtener_contexto_grupos_clientes_activos():
    """Valida contexto minimo para selects de clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})
        crear_grupo_cliente({"nombre": "Inactivo", "activo": 0, "orden": 20})

        contexto = obtener_contexto_grupos_clientes_activos()

    nombres = {grupo["nombre"] for grupo in contexto["grupos_clientes"]}

    assert "Particular" in nombres
    assert "Inactivo" not in nombres
    assert contexto["cantidad_grupos_clientes"] == len(contexto["grupos_clientes"])


def test_obtener_contexto_detalle_grupo_cliente():
    """Valida contexto de detalle para edicion de grupo de clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        contexto = obtener_contexto_detalle_grupo_cliente(str(grupo["id"]))

    assert contexto["grupo_cliente"]["id"] == grupo["id"]
    assert contexto["grupo_cliente"]["nombre"] == "Particular"


def test_obtener_contexto_detalle_grupo_cliente_rechaza_inexistente():
    """Valida rechazo de detalle para grupo inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            obtener_contexto_detalle_grupo_cliente(999)


def test_obtener_grupo_cliente_activo_por_id():
    """Valida obtencion funcional de grupo activo por id."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        grupo_activo = obtener_grupo_cliente_activo_por_id(str(grupo["id"]))

    assert grupo_activo["id"] == grupo["id"]
    assert grupo_activo["esta_activo"] is True


def test_obtener_grupo_cliente_activo_por_id_rechaza_inactivo():
    """Valida que el service no devuelva grupos inactivos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Inactivo", "activo": 0, "orden": 10})

        with pytest.raises(ValueError):
            obtener_grupo_cliente_activo_por_id(grupo["id"])


def test_crear_grupo_cliente_desde_formulario():
    """Valida alta manual de grupo de clientes desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente_desde_formulario(
            {
                "nombre": "  Profesional  ",
                "activo": "1",
                "orden": "30",
            }
        )

    assert grupo["nombre"] == "Profesional"
    assert grupo["activo"] == 1
    assert grupo["orden"] == 30


def test_crear_grupo_cliente_desde_formulario_checkbox_ausente_inactiva():
    """Valida contrato HTML: checkbox ausente equivale a 0."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente_desde_formulario(
            {
                "nombre": "Inactivo",
                "orden": "10",
            }
        )

    assert grupo["activo"] == 0
    assert grupo["esta_activo"] is False


def test_actualizar_grupo_cliente_desde_formulario():
    """Valida edicion manual de grupo de clientes desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        grupo_actualizado = actualizar_grupo_cliente_desde_formulario(
            grupo["id"],
            {
                "nombre": "Particular editado",
                "activo": "1",
                "orden": "15",
            },
        )

    assert grupo_actualizado["id"] == grupo["id"]
    assert grupo_actualizado["nombre"] == "Particular editado"
    assert grupo_actualizado["orden"] == 15


def test_activar_desactivar_grupo_cliente():
    """Valida baja logica por activar/desactivar desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        grupo_desactivado = desactivar_grupo_cliente(grupo["id"])
        grupo_activado = activar_grupo_cliente(grupo["id"])

    assert grupo_desactivado["activo"] == 0
    assert grupo_desactivado["esta_activo"] is False
    assert grupo_activado["activo"] == 1
    assert grupo_activado["esta_activo"] is True


def test_normalizar_id_grupo_cliente_desde_formulario():
    """Valida normalizacion de id recibido desde formulario."""
    assert normalizar_id_grupo_cliente_desde_formulario(" 12 ") == 12


def test_normalizar_id_grupo_cliente_desde_formulario_rechaza_vacio():
    """Valida rechazo de id vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_id_grupo_cliente_desde_formulario("")


def test_normalizar_id_grupo_cliente_desde_formulario_rechaza_no_numerico():
    """Valida rechazo de id no numerico desde formulario."""
    with pytest.raises(ValueError):
        normalizar_id_grupo_cliente_desde_formulario("abc")
