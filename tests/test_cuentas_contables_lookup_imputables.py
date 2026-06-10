from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.cuentas_contables_repository import (
    buscar_cuentas_contables_imputables,
)
from app.contabilidad.cuentas_contables_service import (
    obtener_lookup_cuentas_contables_imputables,
)


def _insertar_cuenta_contable_lookup_test(
    db,
    cuenta,
    descripcion,
    saldo_habitual="DEBE",
    naturaleza="PATRIMONIAL",
    imputable=1,
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


def test_repository_buscar_cuentas_imputables_filtra_por_descripcion_y_estado():
    """
    Valida lookup repository para asientos.

    Solo deben volver cuentas imputables aunque existan sumarizadoras que
    coincidan por descripcion.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_cuenta_contable_lookup_test(
            db,
            "1.1.01.01.000",
            "CAJAS",
            imputable=0,
        )
        _insertar_cuenta_contable_lookup_test(
            db,
            "1.1.01.01.001",
            "CAJA ARS",
            imputable=1,
        )
        _insertar_cuenta_contable_lookup_test(
            db,
            "1.1.01.01.002",
            "CAJA USD",
            imputable=1,
        )

        resultados = buscar_cuentas_contables_imputables("CAJA", limite=10)

    assert [resultado["cuenta"] for resultado in resultados] == [
        "1.1.01.01.001",
        "1.1.01.01.002",
    ]
    assert all(resultado["imputable"] == 1 for resultado in resultados)


def test_repository_buscar_cuentas_imputables_devuelve_vacio_sin_termino():
    """
    Valida que el lookup no devuelva todo el plan ante termino vacio.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_cuenta_contable_lookup_test(
            db,
            "1.1.01.01.001",
            "CAJA ARS",
            imputable=1,
        )

        resultados = buscar_cuentas_contables_imputables("")

    assert resultados == []


def test_service_lookup_cuentas_imputables_formatea_respuesta_json_ready():
    """
    Valida contrato de service para autocomplete.

    El frontend recibira label visible y valor/cuenta para completar el renglon.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_cuenta_contable_lookup_test(
            db,
            "1.1.01.01.001",
            "CAJA ARS",
            imputable=1,
        )

        respuesta = obtener_lookup_cuentas_contables_imputables("ARS")

    assert respuesta["q"] == "ARS"
    assert respuesta["cantidad"] == 1
    assert respuesta["resultados"][0] == {
        "cuenta": "1.1.01.01.001",
        "descripcion": "CAJA ARS",
        "label": "1.1.01.01.001 - CAJA ARS",
        "valor": "1.1.01.01.001",
        "saldo_habitual": "DEBE",
        "naturaleza": "PATRIMONIAL",
        "imputable": 1,
        "monetaria": 1,
        "es_monetaria": True,
    }


def test_route_lookup_cuentas_imputables_devuelve_json():
    """
    Valida endpoint JSON para autocomplete de asientos.

    La route no ejecuta SQL directo y delega busqueda/formato en service.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_cuenta_contable_lookup_test(
            db,
            "1.1.01.01.001",
            "CAJA ARS",
            imputable=1,
        )
        _insertar_cuenta_contable_lookup_test(
            db,
            "1.1.01.01.000",
            "CAJAS",
            imputable=0,
        )

        response = client.get(
            "/contabilidad/cuentas-contables/imputables/buscar/?q=CAJA"
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["q"] == "CAJA"
    assert payload["cantidad"] == 1
    assert payload["resultados"][0]["cuenta"] == "1.1.01.01.001"
    assert payload["resultados"][0]["descripcion"] == "CAJA ARS"


def test_route_lookup_cuentas_imputables_limite_invalido_devuelve_400():
    """
    Valida contrato defensivo del endpoint ante limite invalido.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get(
            "/contabilidad/cuentas-contables/imputables/buscar/?q=CAJA&limite=0"
        )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["q"] == "CAJA"
    assert payload["cantidad"] == 0
    assert payload["resultados"] == []
    assert "limite" in payload["mensaje"]
