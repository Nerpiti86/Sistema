import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.cuentas_contables_repository import (
    obtener_cuenta_contable_por_cuenta,
)
from app.contabilidad.cuentas_contables_service import (
    crear_cuenta_contable_desde_formulario,
)


def test_crear_cuenta_contable_desde_formulario_crea_cuenta_normalizada():
    """
    Valida alta desde formulario delegando persistencia al repository.

    El service no ejecuta SQL: prepara datos de pantalla y retorna la cuenta
    normalizada creada por el repository.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        cuenta_contable = crear_cuenta_contable_desde_formulario(
            {
                "cuenta": " 1.1.01.01.001 ",
                "descripcion": "  CAJA ARS ",
                "saldo_habitual": " debe ",
                "naturaleza": " patrimonial ",
                "imputable": "1",
                "monetaria": "1",
                "sumarizadora": "",
            }
        )

        cuenta_persistida = obtener_cuenta_contable_por_cuenta("1.1.01.01.001")

    assert cuenta_contable["cuenta"] == "1.1.01.01.001"
    assert cuenta_contable["descripcion"] == "CAJA ARS"
    assert cuenta_contable["saldo_habitual"] == "DEBE"
    assert cuenta_contable["naturaleza"] == "PATRIMONIAL"
    assert cuenta_contable["imputable"] == 1
    assert cuenta_contable["monetaria"] == 1
    assert cuenta_contable["sumarizadora"] is None
    assert cuenta_persistida is not None
    assert cuenta_persistida["cuenta"] == "1.1.01.01.001"


def test_crear_cuenta_contable_desde_formulario_rechaza_descripcion_vacia():
    """Valida propagacion de validacion repository para datos de formulario."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="descripcion"):
            crear_cuenta_contable_desde_formulario(
                {
                    "cuenta": "1.1.01.01.001",
                    "descripcion": "",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": "1",
                    "monetaria": "1",
                    "sumarizadora": "",
                }
            )


def test_crear_cuenta_contable_desde_formulario_rechaza_formato_cuenta_invalido():
    """Valida propagacion de formato de cuenta contable al repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="formato 9.9.99.99.999"):
            crear_cuenta_contable_desde_formulario(
                {
                    "cuenta": "1.1.1.01.001",
                    "descripcion": "CAJA ARS",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": "1",
                    "monetaria": "1",
                    "sumarizadora": "",
                }
            )


def test_crear_cuenta_contable_desde_formulario_checkbox_ausente_normaliza_0():
    """
    Valida contrato de checkbox HTML ausente.

    Cuando imputable o monetaria no vienen en el formulario, el service debe
    convertirlos a 0 antes de delegar al repository.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        cuenta_contable = crear_cuenta_contable_desde_formulario(
            {
                "cuenta": "1.1.01.01.001",
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "sumarizadora": "",
            }
        )

    assert cuenta_contable["imputable"] == 0
    assert cuenta_contable["monetaria"] == 0
    assert cuenta_contable["es_imputable"] is False
    assert cuenta_contable["es_monetaria"] is False
