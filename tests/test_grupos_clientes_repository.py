import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.gestion.grupos_clientes_repository import (
    actualizar_grupo_cliente_por_id,
    cambiar_estado_grupo_cliente,
    crear_grupo_cliente,
    listar_grupos_clientes,
    listar_grupos_clientes_activos,
    obtener_grupo_cliente_por_id,
    validar_grupo_cliente_activo,
)


def test_listar_grupos_clientes_devuelve_maestro_ordenado():
    """Valida listado completo del maestro de grupos de clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_grupo_cliente({"nombre": "Mayorista", "activo": 1, "orden": 20})
        crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})
        crear_grupo_cliente({"nombre": "Inactivo", "activo": 0, "orden": 1})

        grupos = listar_grupos_clientes()

    nombres = [grupo["nombre"] for grupo in grupos]

    assert nombres == ["Particular", "Mayorista", "Inactivo"]


def test_listar_grupos_clientes_activos_excluye_inactivos():
    """Valida que el listado operativo solo devuelva grupos activos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})
        crear_grupo_cliente({"nombre": "Inactivo", "activo": 0, "orden": 20})

        grupos = listar_grupos_clientes_activos()

    nombres = {grupo["nombre"] for grupo in grupos}

    assert "Particular" in nombres
    assert "Inactivo" not in nombres


def test_obtener_grupo_cliente_por_id_devuelve_grupo_normalizado():
    """Valida busqueda por id y normalizacion de campos derivados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_creado = crear_grupo_cliente(
            {"nombre": "Particular", "activo": 1, "orden": 10}
        )

        grupo = obtener_grupo_cliente_por_id(str(grupo_creado["id"]))

    assert grupo is not None
    assert grupo["nombre"] == "Particular"
    assert grupo["activo"] == 1
    assert grupo["esta_activo"] is True
    assert grupo["descripcion_select"] == "Particular"


def test_obtener_grupo_cliente_por_id_inexistente_devuelve_none():
    """Valida respuesta nula para grupo inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = obtener_grupo_cliente_por_id(999)

    assert grupo is None


def test_obtener_grupo_cliente_por_id_rechaza_id_invalido():
    """Valida formato funcional de id antes de consultar."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            obtener_grupo_cliente_por_id("abc")


def test_crear_grupo_cliente_normaliza_datos():
    """Valida alta manual de grupo de clientes desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente(
            {"nombre": "  Profesional  ", "activo": "1", "orden": "30"}
        )

    assert grupo["id"] > 0
    assert grupo["nombre"] == "Profesional"
    assert grupo["activo"] == 1
    assert grupo["orden"] == 30
    assert grupo["creado_en"]


def test_crear_grupo_cliente_rechaza_nombre_duplicado_sin_distinguir_mayusculas():
    """Valida unicidad funcional de nombre por COLLATE NOCASE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        with pytest.raises(ValueError):
            crear_grupo_cliente({"nombre": "particular", "activo": 1, "orden": 20})


def test_crear_grupo_cliente_rechaza_nombre_vacio():
    """Valida rechazo de nombre vacio en repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_grupo_cliente({"nombre": "   ", "activo": 1, "orden": 10})


def test_crear_grupo_cliente_rechaza_activo_invalido():
    """Valida rechazo de activo distinto de 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_grupo_cliente({"nombre": "Particular", "activo": 2, "orden": 10})


def test_crear_grupo_cliente_rechaza_orden_negativo():
    """Valida rechazo de orden negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": -1})


def test_actualizar_grupo_cliente_por_id():
    """Valida edicion manual de grupo de clientes desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_creado = crear_grupo_cliente(
            {"nombre": "Particular", "activo": 1, "orden": 10}
        )

        grupo_actualizado = actualizar_grupo_cliente_por_id(
            grupo_creado["id"],
            {"nombre": "Particular editado", "activo": 1, "orden": 15},
        )

    assert grupo_actualizado["id"] == grupo_creado["id"]
    assert grupo_actualizado["nombre"] == "Particular editado"
    assert grupo_actualizado["orden"] == 15
    assert grupo_actualizado["actualizado_en"]


def test_actualizar_grupo_cliente_rechaza_inexistente():
    """Valida rechazo de edicion para grupo inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            actualizar_grupo_cliente_por_id(
                999,
                {"nombre": "Inexistente", "activo": 1, "orden": 10},
            )


def test_cambiar_estado_grupo_cliente():
    """Valida baja logica por activar/desactivar sin borrado fisico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        grupo_desactivado = cambiar_estado_grupo_cliente(grupo["id"], 0)
        grupo_activado = cambiar_estado_grupo_cliente(grupo["id"], 1)

    assert grupo_desactivado["activo"] == 0
    assert grupo_desactivado["esta_activo"] is False
    assert grupo_activado["activo"] == 1
    assert grupo_activado["esta_activo"] is True


def test_validar_grupo_cliente_activo_acepta_activo():
    """Valida grupo existente y activo para operaciones de gestion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 1, "orden": 10})

        resultado = validar_grupo_cliente_activo(grupo["id"])

    assert resultado is True


def test_validar_grupo_cliente_activo_rechaza_inactivo():
    """Valida rechazo de grupo existente pero inactivo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo = crear_grupo_cliente({"nombre": "Particular", "activo": 0, "orden": 10})

        with pytest.raises(ValueError):
            validar_grupo_cliente_activo(grupo["id"])


def test_validar_grupo_cliente_activo_rechaza_inexistente():
    """Valida rechazo de grupo inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            validar_grupo_cliente_activo(999)
