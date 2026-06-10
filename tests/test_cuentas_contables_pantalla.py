from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


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


def test_pantalla_cuentas_contables_responde_ok_sin_datos():
    """
    Valida pantalla de listado sin cuentas cargadas.

    La route usa service y el template mantiene IDs cortos y data-* para
    trazabilidad tecnica de tabla, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/cuentas-contables/")

    assert response.status_code == 200
    assert b"Cuentas contables" in response.data
    assert b"No hay cuentas contables cargadas" in response.data
    assert b'id="cc-listado"' in response.data
    assert b'id="cc-tabla"' in response.data
    assert b'id="cc-mensaje-sin-datos"' in response.data
    assert b'data-table="cuentas_contables"' in response.data
    assert b'data-query="listar_cuentas_contables"' in response.data


def test_pantalla_cuentas_contables_muestra_listado_real():
    """
    Valida listado real de cuentas_contables con datos persistidos.

    El HTML no decide reglas contables: solo renderiza campos recibidos desde
    service/repository.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        response = client.get("/contabilidad/cuentas-contables/")

    assert response.status_code == 200
    assert b"1.1.01.01.001" in response.data
    assert b"CAJA ARS" in response.data
    assert b"DEBE" in response.data
    assert b"PATRIMONIAL" in response.data
    assert b"Si" in response.data
    assert b'id="cc-row-1-1-01-01-001"' in response.data
    assert b'data-row-codigo="1.1.01.01.001"' in response.data
    assert b'data-field="sumarizadora"' in response.data


def test_pantalla_contabilidad_tiene_acceso_a_cuentas_contables():
    """
    Valida acceso desde Contabilidad hacia Cuentas contables.

    El modulo se nombra como Cuentas contables. El contrato jerarquico queda
    separado de la pantalla de acceso.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Cuentas contables" in response.data
    assert b"/contabilidad/cuentas-contables/" in response.data
    assert b'id="cc-acceso"' in response.data
    assert b'data-table="cuentas_contables"' in response.data
