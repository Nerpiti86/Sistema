import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.gestion.paises_repository import (
    actualizar_pais_por_id,
    cambiar_estado_pais,
    crear_pais,
    listar_paises,
    listar_paises_activos,
    obtener_pais_por_id,
    validar_pais_activo,
)


def test_listar_paises_devuelve_maestro_ordenado():
    """Valida listado completo del maestro comun de paises."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_pais({"nombre": "Uruguay", "codigo_iso": "UY", "activo": 1, "orden": 20})
        crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})
        crear_pais({"nombre": "Inactivo", "codigo_iso": None, "activo": 0, "orden": 1})

        paises = listar_paises()

    nombres = [pais["nombre"] for pais in paises]

    assert nombres == ["Argentina", "Uruguay", "Inactivo"]


def test_listar_paises_activos_excluye_inactivos():
    """Valida que el listado operativo solo devuelva paises activos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})
        crear_pais({"nombre": "Inactivo", "codigo_iso": None, "activo": 0, "orden": 20})

        paises = listar_paises_activos()

    nombres = {pais["nombre"] for pais in paises}

    assert "Argentina" in nombres
    assert "Inactivo" not in nombres


def test_obtener_pais_por_id_devuelve_pais_normalizado():
    """Valida busqueda por id y normalizacion de campos derivados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais_creado = crear_pais(
            {"nombre": "Argentina", "codigo_iso": "ar", "activo": 1, "orden": 10}
        )

        pais = obtener_pais_por_id(str(pais_creado["id"]))

    assert pais is not None
    assert pais["nombre"] == "Argentina"
    assert pais["codigo_iso"] == "AR"
    assert pais["activo"] == 1
    assert pais["esta_activo"] is True
    assert pais["descripcion_select"] == "Argentina (AR)"


def test_obtener_pais_por_id_inexistente_devuelve_none():
    """Valida respuesta nula para pais inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = obtener_pais_por_id(999)

    assert pais is None


def test_obtener_pais_por_id_rechaza_id_invalido():
    """Valida formato funcional de id antes de consultar."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            obtener_pais_por_id("abc")


def test_crear_pais_normaliza_datos():
    """Valida alta manual de pais desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais(
            {
                "nombre": "  Argentina  ",
                "codigo_iso": " ar ",
                "activo": "1",
                "orden": "30",
            }
        )

    assert pais["id"] > 0
    assert pais["nombre"] == "Argentina"
    assert pais["codigo_iso"] == "AR"
    assert pais["activo"] == 1
    assert pais["orden"] == 30
    assert pais["creado_en"]


def test_crear_pais_permite_codigo_iso_vacio():
    """Valida que codigo_iso sea opcional desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais(
            {"nombre": "Argentina", "codigo_iso": "   ", "activo": 1, "orden": 10}
        )

    assert pais["codigo_iso"] is None
    assert pais["descripcion_select"] == "Argentina"


def test_crear_pais_rechaza_nombre_duplicado_sin_distinguir_mayusculas():
    """Valida unicidad funcional de nombre por COLLATE NOCASE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})

        with pytest.raises(ValueError):
            crear_pais(
                {"nombre": "argentina", "codigo_iso": "ARG", "activo": 1, "orden": 20}
            )


def test_crear_pais_rechaza_codigo_iso_duplicado_sin_distinguir_mayusculas():
    """Valida unicidad funcional de codigo_iso por COLLATE NOCASE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})

        with pytest.raises(ValueError):
            crear_pais(
                {
                    "nombre": "Republica Argentina",
                    "codigo_iso": "ar",
                    "activo": 1,
                    "orden": 20,
                }
            )


def test_crear_pais_rechaza_nombre_vacio():
    """Valida rechazo de nombre vacio en repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_pais({"nombre": "   ", "codigo_iso": "AR", "activo": 1, "orden": 10})


def test_crear_pais_rechaza_codigo_iso_largo_invalido():
    """Valida rechazo de codigo_iso con largo distinto de 2 o 3."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_pais(
                {"nombre": "Argentina", "codigo_iso": "ARGEN", "activo": 1, "orden": 10}
            )


def test_crear_pais_rechaza_activo_invalido():
    """Valida rechazo de activo distinto de 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 2, "orden": 10})


def test_crear_pais_rechaza_orden_negativo():
    """Valida rechazo de orden negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": -1})


def test_actualizar_pais_por_id():
    """Valida edicion manual de pais desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais_creado = crear_pais(
            {"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10}
        )

        pais_actualizado = actualizar_pais_por_id(
            pais_creado["id"],
            {"nombre": "Argentina editado", "codigo_iso": "ARG", "activo": 1, "orden": 15},
        )

    assert pais_actualizado["id"] == pais_creado["id"]
    assert pais_actualizado["nombre"] == "Argentina editado"
    assert pais_actualizado["codigo_iso"] == "ARG"
    assert pais_actualizado["orden"] == 15
    assert pais_actualizado["actualizado_en"]


def test_actualizar_pais_rechaza_inexistente():
    """Valida rechazo de edicion para pais inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            actualizar_pais_por_id(
                999,
                {"nombre": "Inexistente", "codigo_iso": "ZZ", "activo": 1, "orden": 10},
            )


def test_cambiar_estado_pais():
    """Valida baja logica por activar/desactivar sin borrado fisico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})

        pais_desactivado = cambiar_estado_pais(pais["id"], 0)
        pais_activado = cambiar_estado_pais(pais["id"], 1)

    assert pais_desactivado["activo"] == 0
    assert pais_desactivado["esta_activo"] is False
    assert pais_activado["activo"] == 1
    assert pais_activado["esta_activo"] is True


def test_validar_pais_activo_acepta_activo():
    """Valida pais existente y activo para operaciones de gestion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais({"nombre": "Argentina", "codigo_iso": "AR", "activo": 1, "orden": 10})

        resultado = validar_pais_activo(pais["id"])

    assert resultado is True


def test_validar_pais_activo_rechaza_inactivo():
    """Valida rechazo de pais existente pero inactivo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        pais = crear_pais({"nombre": "Inactivo", "codigo_iso": None, "activo": 0, "orden": 10})

        with pytest.raises(ValueError):
            validar_pais_activo(pais["id"])


def test_validar_pais_activo_rechaza_inexistente():
    """Valida rechazo de pais inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            validar_pais_activo(999)
