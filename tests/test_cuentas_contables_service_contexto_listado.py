import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.cuentas_contables_service import (
    obtener_contexto_detalle_cuenta_contable,
    obtener_contexto_listado_cuentas_contables,
)


def _insertar_cuenta_contable_para_test(
    db,
    cuenta,
    descripcion,
    saldo_habitual="DEBE",
    naturaleza="PATRIMONIAL",
    imputable=0,
    monetaria=1,
    sumarizadora=None,
):
    db.execute(
        """
        INSERT INTO cuentas_contables (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            sumarizadora,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            sumarizadora,
            "2026-01-01 10:00:00",
        ),
    )


def _insertar_jerarquia_caja_ars_para_test(db):
    _insertar_cuenta_contable_para_test(
        db,
        "1.0.00.00.000",
        "ACTIVO",
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.00.00.000",
        "ACTIVO CORRIENTE",
        sumarizadora="1.0.00.00.000",
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.01.00.000",
        "CAJAS Y BANCOS",
        sumarizadora="1.1.00.00.000",
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.01.01.000",
        "CAJAS",
        sumarizadora="1.1.01.00.000",
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.01.01.001",
        "CAJA ARS",
        imputable=1,
        sumarizadora="1.1.01.01.000",
    )


def test_obtener_contexto_listado_cuentas_contables_devuelve_contexto_chico():
    """Valida contexto de pantalla sin cargar datos operativos vinculados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        contexto_listado = obtener_contexto_listado_cuentas_contables()

    assert contexto_listado["cantidad_cuentas_contables"] == 5
    assert contexto_listado["cuentas_contables"][0]["cuenta"] == "1.0.00.00.000"
    assert contexto_listado["cuentas_contables"][-1]["cuenta"] == "1.1.01.01.001"


def test_obtener_contexto_detalle_cuenta_contable_devuelve_contexto_chico():
    """Valida contexto de detalle delegado al repository por cuenta."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        contexto_detalle = obtener_contexto_detalle_cuenta_contable(
            "1.1.01.01.001"
        )

    cuenta_contable = contexto_detalle["cuenta_contable"]

    assert cuenta_contable["cuenta"] == "1.1.01.01.001"
    assert cuenta_contable["descripcion"] == "CAJA ARS"
    assert cuenta_contable["imputable"] == 1
    assert cuenta_contable["sumarizadora"] == "1.1.01.01.000"


def test_obtener_contexto_detalle_cuenta_contable_rechaza_faltante():
    """Valida que el service no invente una cuenta inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe la cuenta contable"):
            obtener_contexto_detalle_cuenta_contable("9.9.99.99.999")


def test_obtener_contexto_detalle_cuenta_contable_rechaza_vacia():
    """Valida entrada obligatoria antes de delegar al repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="obligatoria"):
            obtener_contexto_detalle_cuenta_contable("")
