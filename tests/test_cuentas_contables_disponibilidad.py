from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _insertar_cuenta_contable_para_disponibilidad_test(
    db,
    cuenta,
    descripcion,
    saldo_habitual="DEBE",
    naturaleza="PATRIMONIAL",
    imputable=0,
    monetaria=0,
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


def test_disponibilidad_cuenta_contable_ocupada_devuelve_json():
    """
    Valida endpoint JSON para cuenta ocupada.

    La route no ejecuta SQL directo: delega en service y devuelve estado de
    disponibilidad para que el JS bloquee el alta si el codigo ya existe.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_cuenta_contable_para_disponibilidad_test(
            db,
            "1.1.01.01.001",
            "CAJA ARS",
        )

        response = client.get(
            "/contabilidad/cuentas-contables/disponibilidad/1.1.01.01.001/"
        )

    assert response.status_code == 200
    assert response.get_json() == {
        "cuenta": "1.1.01.01.001",
        "disponible": False,
        "ocupada": True,
        "descripcion": "CAJA ARS",
        "mensaje": "La cuenta contable ya esta ocupada.",
    }


def test_disponibilidad_cuenta_contable_libre_devuelve_json():
    """
    Valida endpoint JSON para cuenta libre.

    Si el codigo no existe, la respuesta informa disponible=True para permitir
    continuar la carga de la nueva cuenta contable.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get(
            "/contabilidad/cuentas-contables/disponibilidad/1.1.01.01.001/"
        )

    assert response.status_code == 200
    assert response.get_json() == {
        "cuenta": "1.1.01.01.001",
        "disponible": True,
        "ocupada": False,
        "descripcion": "",
        "mensaje": "Cuenta contable disponible.",
    }


def test_disponibilidad_cuenta_contable_formato_invalido_devuelve_400():
    """
    Valida respuesta para formato invalido.

    Aunque el JS evita consultar si el formato no es valido, la route mantiene
    contrato defensivo para solicitudes manuales o integraciones futuras.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get(
            "/contabilidad/cuentas-contables/disponibilidad/1.1/"
        )

    assert response.status_code == 400
    assert response.get_json() == {
        "cuenta": "1.1",
        "disponible": False,
        "ocupada": False,
        "descripcion": "",
        "mensaje": "La cuenta contable debe respetar el formato 9.9.99.99.999.",
    }


def test_formulario_alta_expone_validacion_disponibilidad_cuenta_contable():
    """
    Valida contrato HTML para disponibilidad al vuelo.

    El alta de cuentas_contables debe exponer data-hooks y cargar JS separado
    para validar si el codigo de cuenta ya esta ocupado antes del submit.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/cuentas-contables/nueva/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="cc-cuenta"' in html
    assert 'data-disponibilidad="cuentas-contables-cuenta-disponible"' in html
    assert "disponibilidad/__CUENTA_CONTABLE__/" in html
    assert "js/cuentas_contables_form_disponibilidad.js" in html


def test_js_disponibilidad_cuenta_contable_tiene_nombres_identificables():
    """
    Valida que el JS separado use nombres especificos.

    La disponibilidad al vuelo debe quedar aislada y reconocible para no mezclar
    validacion de formato, lookup de sumarizadora y reglas de pantalla.
    """
    js = "app/static/js/cuentas_contables_form_disponibilidad.js"

    with open(js, encoding="utf-8") as archivo_js:
        contenido = archivo_js.read()

    assert "CUENTAS_CONTABLES_SELECTOR_DISPONIBILIDAD" in contenido
    assert "validarDisponibilidadCuentaContable" in contenido
    assert "aplicarCuentaContableOcupada" in contenido
    assert "aplicarCuentaContableDisponible" in contenido
    assert "inicializarDisponibilidadCuentaContable" in contenido
