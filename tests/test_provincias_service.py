from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.shared.paises_repository import crear_pais
from app.shared.provincias_repository import crear_provincia
from app.shared.provincias_service import (
    activar_provincia,
    actualizar_provincia_desde_formulario,
    crear_provincia_desde_formulario,
    desactivar_provincia,
    normalizar_id_pais_desde_formulario,
    normalizar_id_provincia_desde_formulario,
    obtener_contexto_detalle_provincia,
    obtener_contexto_formulario_provincia,
    obtener_contexto_listado_provincias,
    obtener_contexto_provincias_activas_por_pais,
    obtener_contexto_provincias_por_pais,
    obtener_provincia_activa_por_id,
)


def _crear_pais(nombre="Argentina", codigo_iso="AR", activo=1, orden=10):
    return crear_pais(
        {
            "nombre": nombre,
            "codigo_iso": codigo_iso,
            "activo": activo,
            "orden": orden,
        }
    )


def test_provincias_service_no_usa_sql_directo():
    """Valida que el service de provincias no ejecute SQL ni use get_db."""
    contenido = Path("app/shared/provincias_service.py").read_text(encoding="utf-8")

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_obtener_contexto_listado_provincias():
    """Valida contexto completo del maestro provincias."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )
        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Inactiva", "activo": 0, "orden": 20}
        )

        contexto = obtener_contexto_listado_provincias()

    assert contexto["cantidad_provincias"] == 2
    assert contexto["cantidad_provincias_activas"] == 1
    assert {"provincias", "provincias_activas"}.issubset(contexto)


def test_obtener_contexto_provincias_por_pais():
    """Valida contexto de provincias por pais activo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais("Argentina", "AR")
        uruguay = _crear_pais("Uruguay", "UY")
        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )
        crear_provincia(
            {"pais_id": uruguay["id"], "nombre": "Montevideo", "activo": 1, "orden": 10}
        )

        contexto = obtener_contexto_provincias_por_pais(argentina["id"])

    nombres = {provincia["nombre"] for provincia in contexto["provincias"]}

    assert contexto["pais_id"] == argentina["id"]
    assert nombres == {"Santa Fe"}


def test_obtener_contexto_provincias_por_pais_rechaza_pais_inactivo():
    """Valida que el service no liste provincias de pais inactivo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = _crear_pais("Pais inactivo", "PI", activo=0)

        with pytest.raises(ValueError):
            obtener_contexto_provincias_por_pais(pais["id"])


def test_obtener_contexto_provincias_activas_por_pais():
    """Valida contexto minimo de provincias activas por pais."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )
        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Inactiva", "activo": 0, "orden": 20}
        )

        contexto = obtener_contexto_provincias_activas_por_pais(argentina["id"])

    nombres = {provincia["nombre"] for provincia in contexto["provincias"]}

    assert "Santa Fe" in nombres
    assert "Inactiva" not in nombres


def test_obtener_contexto_formulario_provincia():
    """Valida contexto de formulario con paises activos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _crear_pais("Argentina", "AR", activo=1)
        _crear_pais("Inactivo", "II", activo=0)

        contexto = obtener_contexto_formulario_provincia()

    nombres_paises = {pais["nombre"] for pais in contexto["paises"]}

    assert "Argentina" in nombres_paises
    assert "Inactivo" not in nombres_paises
    assert contexto["provincia"]["activo"] == 1
    assert contexto["provincia"]["orden"] == 0


def test_obtener_contexto_detalle_provincia():
    """Valida contexto de detalle para edicion de provincia."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        contexto = obtener_contexto_detalle_provincia(str(provincia["id"]))

    assert contexto["provincia"]["id"] == provincia["id"]
    assert contexto["provincia"]["nombre"] == "Santa Fe"


def test_obtener_contexto_detalle_provincia_rechaza_inexistente():
    """Valida rechazo de detalle para provincia inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            obtener_contexto_detalle_provincia(999)


def test_obtener_provincia_activa_por_id():
    """Valida obtencion funcional de provincia activa por id."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        provincia_activa = obtener_provincia_activa_por_id(str(provincia["id"]))

    assert provincia_activa["id"] == provincia["id"]
    assert provincia_activa["esta_activa"] is True


def test_obtener_provincia_activa_por_id_rechaza_inactiva():
    """Valida que el service no devuelva provincias inactivas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Inactiva", "activo": 0, "orden": 10}
        )

        with pytest.raises(ValueError):
            obtener_provincia_activa_por_id(provincia["id"])


def test_crear_provincia_desde_formulario():
    """Valida alta manual de provincia desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia_desde_formulario(
            {
                "pais_id": str(argentina["id"]),
                "nombre": "  Santa Fe  ",
                "activo": "1",
                "orden": "30",
            }
        )

    assert provincia["pais_id"] == argentina["id"]
    assert provincia["nombre"] == "Santa Fe"
    assert provincia["activo"] == 1
    assert provincia["orden"] == 30


def test_crear_provincia_desde_formulario_rechaza_pais_inactivo():
    """Valida rechazo de alta contra pais inactivo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = _crear_pais("Pais inactivo", "PI", activo=0)

        with pytest.raises(ValueError):
            crear_provincia_desde_formulario(
                {
                    "pais_id": str(pais["id"]),
                    "nombre": "Provincia",
                    "activo": "1",
                    "orden": "10",
                }
            )


def test_crear_provincia_desde_formulario_checkbox_ausente_inactiva():
    """Valida contrato HTML: checkbox ausente equivale a 0."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia_desde_formulario(
            {
                "pais_id": str(argentina["id"]),
                "nombre": "Inactiva",
                "orden": "10",
            }
        )

    assert provincia["activo"] == 0
    assert provincia["esta_activa"] is False


def test_actualizar_provincia_desde_formulario():
    """Valida edicion manual de provincia desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        provincia_actualizada = actualizar_provincia_desde_formulario(
            provincia["id"],
            {
                "pais_id": str(argentina["id"]),
                "nombre": "Santa Fe editada",
                "activo": "1",
                "orden": "15",
            },
        )

    assert provincia_actualizada["id"] == provincia["id"]
    assert provincia_actualizada["nombre"] == "Santa Fe editada"
    assert provincia_actualizada["orden"] == 15


def test_activar_desactivar_provincia():
    """Valida baja logica por activar/desactivar desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        provincia_desactivada = desactivar_provincia(provincia["id"])
        provincia_activada = activar_provincia(provincia["id"])

    assert provincia_desactivada["activo"] == 0
    assert provincia_desactivada["esta_activa"] is False
    assert provincia_activada["activo"] == 1
    assert provincia_activada["esta_activa"] is True


def test_normalizar_id_provincia_desde_formulario():
    """Valida normalizacion de id recibido desde formulario."""
    assert normalizar_id_provincia_desde_formulario(" 12 ") == 12


def test_normalizar_id_provincia_desde_formulario_rechaza_vacio():
    """Valida rechazo de id vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_id_provincia_desde_formulario("")


def test_normalizar_id_provincia_desde_formulario_rechaza_no_numerico():
    """Valida rechazo de id no numerico desde formulario."""
    with pytest.raises(ValueError):
        normalizar_id_provincia_desde_formulario("abc")


def test_normalizar_id_pais_desde_formulario():
    """Valida normalizacion de id de pais recibido desde formulario."""
    assert normalizar_id_pais_desde_formulario(" 7 ") == 7


def test_normalizar_id_pais_desde_formulario_rechaza_vacio():
    """Valida rechazo de id de pais vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_id_pais_desde_formulario("")
