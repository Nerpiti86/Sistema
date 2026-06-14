import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.shared.catalogos_fiscales_repository import (
    actualizar_item_catalogo_fiscal_por_codigo,
    cambiar_estado_item_catalogo_fiscal,
    crear_item_catalogo_fiscal,
    listar_catalogo_fiscal,
    obtener_item_catalogo_fiscal_por_codigo,
)


def test_catalogos_fiscales_repository_lista_semillas():
    """Valida lectura repository de catalogos fiscales iniciales."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        condiciones = listar_catalogo_fiscal("condiciones_iva")
        tipos = listar_catalogo_fiscal("tipos_documento")

    assert condiciones[0]["codigo"] == "1"
    assert any(item["descripcion"] == "Consumidor Final" for item in condiciones)
    assert any(item["codigo"] == "80" and item["descripcion"] == "CUIT" for item in tipos)


def test_catalogos_fiscales_repository_abm_basico():
    """Valida alta, edicion y baja logica de catalogo fiscal generico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        item = crear_item_catalogo_fiscal(
            "tipos_documento",
            {
                "codigo": "77",
                "descripcion": "Documento prueba",
                "activo": 1,
                "orden": 70,
            },
        )
        actualizado = actualizar_item_catalogo_fiscal_por_codigo(
            "tipos_documento",
            "77",
            {
                "descripcion": "Documento prueba editado",
                "activo": 1,
                "orden": 71,
            },
        )
        desactivado = cambiar_estado_item_catalogo_fiscal("tipos_documento", "77", 0)
        recuperado = obtener_item_catalogo_fiscal_por_codigo("tipos_documento", "77")

    assert item["codigo"] == "77"
    assert actualizado["descripcion"] == "Documento prueba editado"
    assert desactivado["activo"] == 0
    assert recuperado["esta_activo"] is False


def test_catalogos_fiscales_repository_rechaza_catalogo_invalido():
    """Valida que no se pueda acceder a tablas fuera del contrato permitido."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        with pytest.raises(ValueError, match="Catalogo fiscal invalido"):
            listar_catalogo_fiscal("tabla_inexistente")
