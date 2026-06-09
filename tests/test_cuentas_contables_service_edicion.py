import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.cuentas_contables_repository import (
    crear_cuenta_contable,
    obtener_cuenta_contable_por_cuenta,
)
from app.contabilidad.cuentas_contables_service import (
    actualizar_cuenta_contable_desde_formulario,
)


def test_actualizar_cuenta_contable_desde_formulario_actualiza_normalizado():
    """
    Valida edicion desde formulario delegando persistencia al repository.

    El service no ejecuta SQL: prepara datos de pantalla y retorna la cuenta
    normalizada actualizada por el repository.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_cuenta_contable(
            {
                "cuenta": "1.1.01.01.001",
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": "1",
                "monetaria": "1",
                "sumarizadora": None,
            }
        )

        cuenta_contable = actualizar_cuenta_contable_desde_formulario(
            "1.1.01.01.001",
            {
                "cuenta": "1.1.01.01.999",
                "descripcion": "  CAJA PESOS ",
                "saldo_habitual": " debe ",
                "naturaleza": " patrimonial ",
                "imputable": "1",
                "monetaria": " no ",
                "sumarizadora": "",
            },
        )

        cuenta_persistida = obtener_cuenta_contable_por_cuenta("1.1.01.01.001")
        cuenta_codigo_formulario = obtener_cuenta_contable_por_cuenta("1.1.01.01.999")

    assert cuenta_contable["cuenta"] == "1.1.01.01.001"
    assert cuenta_contable["descripcion"] == "CAJA PESOS"
    assert cuenta_contable["saldo_habitual"] == "DEBE"
    assert cuenta_contable["naturaleza"] == "PATRIMONIAL"
    assert cuenta_contable["imputable"] == 1
    assert cuenta_contable["monetaria"] == 0
    assert cuenta_contable["sumarizadora"] is None
    assert cuenta_persistida is not None
    assert cuenta_persistida["descripcion"] == "CAJA PESOS"
    assert cuenta_codigo_formulario is None


def test_actualizar_cuenta_contable_desde_formulario_rechaza_inexistente():
    """Valida propagacion de inexistencia desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe la cuenta contable"):
            actualizar_cuenta_contable_desde_formulario(
                "9.9.99.99.999",
                {
                    "descripcion": "NO EXISTE",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": "1",
                    "monetaria": "1",
                    "sumarizadora": "",
                },
            )


def test_actualizar_cuenta_contable_desde_formulario_rechaza_descripcion_vacia():
    """Valida propagacion de validacion repository para datos de formulario."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_cuenta_contable(
            {
                "cuenta": "1.1.01.01.001",
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": "1",
                "monetaria": "1",
                "sumarizadora": None,
            }
        )

        with pytest.raises(ValueError, match="descripcion"):
            actualizar_cuenta_contable_desde_formulario(
                "1.1.01.01.001",
                {
                    "descripcion": "",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": "1",
                    "monetaria": "1",
                    "sumarizadora": "",
                },
            )
