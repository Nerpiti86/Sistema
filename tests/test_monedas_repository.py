import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.monedas_repository import (
    listar_monedas,
    listar_monedas_activas,
    obtener_moneda_por_codigo,
    validar_moneda_activa,
)


def test_listar_monedas_devuelve_maestro_ordenado():
    """Valida listado completo del maestro transversal monedas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        monedas = listar_monedas()

    codigos = [moneda["codigo"] for moneda in monedas]

    assert codigos[:3] == ["ARS", "USD", "EUR"]


def test_listar_monedas_activas_excluye_inactivas():
    """Valida que el listado operativo solo devuelva monedas activas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            "UPDATE monedas SET activa = 0 WHERE codigo = ?",
            ("EUR",),
        )

        monedas = listar_monedas_activas()

    codigos = {moneda["codigo"] for moneda in monedas}

    assert "ARS" in codigos
    assert "USD" in codigos
    assert "EUR" not in codigos


def test_obtener_moneda_por_codigo_normaliza_codigo():
    """Valida busqueda por codigo normalizando mayusculas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        moneda = obtener_moneda_por_codigo("ars")

    assert moneda is not None
    assert moneda["codigo"] == "ARS"
    assert moneda["esta_activa"] is True
    assert moneda["descripcion_select"] == "ARS - Peso argentino"


def test_obtener_moneda_por_codigo_inexistente_devuelve_none():
    """Valida respuesta nula para moneda inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        moneda = obtener_moneda_por_codigo("GBP")

    assert moneda is None


def test_obtener_moneda_por_codigo_rechaza_codigo_invalido():
    """Valida formato funcional AAA antes de consultar."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            obtener_moneda_por_codigo("AR")


def test_validar_moneda_activa_acepta_moneda_activa():
    """Valida moneda existente y activa para operaciones."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        resultado = validar_moneda_activa("USD")

    assert resultado is True


def test_validar_moneda_activa_rechaza_inexistente():
    """Valida rechazo de moneda no cargada."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            validar_moneda_activa("GBP")


def test_validar_moneda_activa_rechaza_inactiva():
    """Valida rechazo de moneda existente pero inactiva."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            "UPDATE monedas SET activa = 0 WHERE codigo = ?",
            ("USD",),
        )

        with pytest.raises(ValueError):
            validar_moneda_activa("USD")
