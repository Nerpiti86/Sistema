import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.shared.paises_repository import crear_pais
from app.shared.provincias_repository import (
    actualizar_provincia_por_id,
    cambiar_estado_provincia,
    crear_provincia,
    listar_provincias,
    listar_provincias_activas_por_pais,
    listar_provincias_por_pais,
    obtener_provincia_por_id,
    validar_provincia_activa,
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


def test_listar_provincias_devuelve_maestro_ordenado():
    """Valida listado completo del maestro comun de provincias."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais("Argentina", "AR", 1, 10)
        uruguay = _crear_pais("Uruguay", "UY", 1, 20)

        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 20}
        )
        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Buenos Aires", "activo": 1, "orden": 10}
        )
        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Inactivo", "activo": 0, "orden": 1}
        )
        crear_provincia(
            {"pais_id": uruguay["id"], "nombre": "Montevideo", "activo": 1, "orden": 10}
        )

        provincias = listar_provincias()

    nombres = [provincia["nombre"] for provincia in provincias]

    assert nombres == ["Buenos Aires", "Santa Fe", "Inactivo", "Montevideo"]


def test_listar_provincias_por_pais_filtra_pais():
    """Valida listado completo de provincias por pais."""
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

        provincias = listar_provincias_por_pais(argentina["id"])

    nombres = {provincia["nombre"] for provincia in provincias}

    assert nombres == {"Santa Fe"}


def test_listar_provincias_activas_por_pais_excluye_inactivas():
    """Valida que el listado operativo por pais solo devuelva provincias activas."""
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

        provincias = listar_provincias_activas_por_pais(argentina["id"])

    nombres = {provincia["nombre"] for provincia in provincias}

    assert "Santa Fe" in nombres
    assert "Inactiva" not in nombres


def test_obtener_provincia_por_id_devuelve_provincia_normalizada():
    """Valida busqueda por id y normalizacion de campos derivados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia_creada = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        provincia = obtener_provincia_por_id(str(provincia_creada["id"]))

    assert provincia is not None
    assert provincia["nombre"] == "Santa Fe"
    assert provincia["pais_id"] == argentina["id"]
    assert provincia["pais_nombre"] == "Argentina"
    assert provincia["pais_codigo_iso"] == "AR"
    assert provincia["pais_descripcion"] == "Argentina (AR)"
    assert provincia["activo"] == 1
    assert provincia["esta_activa"] is True
    assert provincia["descripcion_select"] == "Santa Fe"


def test_obtener_provincia_por_id_inexistente_devuelve_none():
    """Valida respuesta nula para provincia inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        provincia = obtener_provincia_por_id(999)

    assert provincia is None


def test_obtener_provincia_por_id_rechaza_id_invalido():
    """Valida formato funcional de id antes de consultar."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            obtener_provincia_por_id("abc")


def test_crear_provincia_normaliza_datos():
    """Valida alta manual de provincia desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {
                "pais_id": str(argentina["id"]),
                "nombre": "  Santa Fe  ",
                "activo": "1",
                "orden": "30",
            }
        )

    assert provincia["id"] > 0
    assert provincia["pais_id"] == argentina["id"]
    assert provincia["nombre"] == "Santa Fe"
    assert provincia["activo"] == 1
    assert provincia["orden"] == 30
    assert provincia["creado_en"]


def test_crear_provincia_rechaza_pais_inexistente():
    """Valida rechazo por FK cuando el pais no existe."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_provincia(
                {"pais_id": 999, "nombre": "Santa Fe", "activo": 1, "orden": 10}
            )


def test_crear_provincia_rechaza_nombre_duplicado_en_mismo_pais():
    """Valida unicidad funcional de nombre por pais."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()

        crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        with pytest.raises(ValueError):
            crear_provincia(
                {"pais_id": argentina["id"], "nombre": "santa fe", "activo": 1, "orden": 20}
            )


def test_crear_provincia_permite_mismo_nombre_en_distinto_pais():
    """Valida que dos paises puedan tener provincia con igual nombre."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais("Argentina", "AR")
        uruguay = _crear_pais("Uruguay", "UY")

        provincia_argentina = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )
        provincia_uruguay = crear_provincia(
            {"pais_id": uruguay["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

    assert provincia_argentina["id"] != provincia_uruguay["id"]


def test_crear_provincia_rechaza_nombre_vacio():
    """Valida rechazo de nombre vacio en repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()

        with pytest.raises(ValueError):
            crear_provincia(
                {"pais_id": argentina["id"], "nombre": "   ", "activo": 1, "orden": 10}
            )


def test_crear_provincia_rechaza_activo_invalido():
    """Valida rechazo de activo distinto de 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()

        with pytest.raises(ValueError):
            crear_provincia(
                {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 2, "orden": 10}
            )


def test_crear_provincia_rechaza_orden_negativo():
    """Valida rechazo de orden negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()

        with pytest.raises(ValueError):
            crear_provincia(
                {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": -1}
            )


def test_actualizar_provincia_por_id():
    """Valida edicion manual de provincia desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia_creada = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        provincia_actualizada = actualizar_provincia_por_id(
            provincia_creada["id"],
            {
                "pais_id": argentina["id"],
                "nombre": "Santa Fe editada",
                "activo": 1,
                "orden": 15,
            },
        )

    assert provincia_actualizada["id"] == provincia_creada["id"]
    assert provincia_actualizada["nombre"] == "Santa Fe editada"
    assert provincia_actualizada["orden"] == 15
    assert provincia_actualizada["actualizado_en"]


def test_actualizar_provincia_rechaza_inexistente():
    """Valida rechazo de edicion para provincia inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()

        with pytest.raises(ValueError):
            actualizar_provincia_por_id(
                999,
                {
                    "pais_id": argentina["id"],
                    "nombre": "Inexistente",
                    "activo": 1,
                    "orden": 10,
                },
            )


def test_cambiar_estado_provincia():
    """Valida baja logica por activar/desactivar sin borrado fisico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        provincia_desactivada = cambiar_estado_provincia(provincia["id"], 0)
        provincia_activada = cambiar_estado_provincia(provincia["id"], 1)

    assert provincia_desactivada["activo"] == 0
    assert provincia_desactivada["esta_activa"] is False
    assert provincia_activada["activo"] == 1
    assert provincia_activada["esta_activa"] is True


def test_validar_provincia_activa_acepta_activa():
    """Valida provincia existente y activa para operaciones de gestion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Santa Fe", "activo": 1, "orden": 10}
        )

        resultado = validar_provincia_activa(provincia["id"])

    assert resultado is True


def test_validar_provincia_activa_rechaza_inactiva():
    """Valida rechazo de provincia existente pero inactiva."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        argentina = _crear_pais()
        provincia = crear_provincia(
            {"pais_id": argentina["id"], "nombre": "Inactiva", "activo": 0, "orden": 10}
        )

        with pytest.raises(ValueError):
            validar_provincia_activa(provincia["id"])


def test_validar_provincia_activa_rechaza_inexistente():
    """Valida rechazo de provincia inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            validar_provincia_activa(999)
