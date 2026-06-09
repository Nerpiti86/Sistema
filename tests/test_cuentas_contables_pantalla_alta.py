from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_pantalla_nueva_cuenta_contable_responde_ok():
    """
    Valida formulario de alta con IDs cortos y data-* estables.

    La pantalla no ejecuta SQL directo: solo expone campos del contrato de
    cuentas_contables para que la route delegue al service.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/cuentas-contables/nueva/")

    assert response.status_code == 200
    assert b"Nueva cuenta contable" in response.data
    assert b'id="cc-form"' in response.data
    assert b'id="cc-formulario"' in response.data
    assert b'id="cc-cuenta"' in response.data
    assert b'id="cc-descripcion-input"' in response.data
    assert b'id="cc-saldo-habitual"' in response.data
    assert b'id="cc-naturaleza"' in response.data
    assert b'id="cc-imputable"' in response.data
    assert b'id="cc-monetaria"' in response.data
    assert b'id="cc-sumarizadora"' in response.data
    assert b'id="cc-guardar"' in response.data
    assert b'data-action="crear_cuenta_contable"' in response.data
    assert b'data-field="cuenta"' in response.data


def test_crear_cuenta_contable_desde_pantalla_redirige_a_listado():
    """
    Valida POST de alta sin SQL en route.

    La route recibe formulario, delega al service y redirige al listado despues
    de crear la cuenta contable.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.post(
            "/contabilidad/cuentas-contables/nueva/",
            data={
                "cuenta": "1.1.01.01.001",
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": "1",
                "monetaria": "1",
                "sumarizadora": "",
            },
            follow_redirects=False,
        )

        db = get_db()
        cuenta_creada = db.execute(
            """
            SELECT cuenta, descripcion
            FROM cuentas_contables
            WHERE cuenta = ?
            LIMIT 1
            """,
            ("1.1.01.01.001",),
        ).fetchone()

    assert response.status_code == 302
    assert "/contabilidad/cuentas-contables/" in response.headers["Location"]
    assert cuenta_creada is not None
    assert cuenta_creada["cuenta"] == "1.1.01.01.001"
    assert cuenta_creada["descripcion"] == "CAJA ARS"


def test_crear_cuenta_contable_desde_pantalla_muestra_error_validacion():
    """
    Valida POST invalido manteniendo formulario y status 400.

    El mensaje viene del service/repository, no de reglas contables en template.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.post(
            "/contabilidad/cuentas-contables/nueva/",
            data={
                "cuenta": "1.1.1.01.001",
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": "1",
                "monetaria": "1",
                "sumarizadora": "",
            },
        )

    assert response.status_code == 400
    assert b"Nueva cuenta contable" in response.data
    assert b"formato 9.9.99.99.999" in response.data


def test_listado_cuentas_contables_tiene_boton_nueva():
    """Valida acceso desde listado al formulario de alta."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/cuentas-contables/")

    assert response.status_code == 200
    assert b'id="cc-nueva"' in response.data
    assert b"/contabilidad/cuentas-contables/nueva/" in response.data
    assert b'data-action="crear_cuenta_contable"' in response.data


def test_formulario_cuenta_contable_muestra_flags_como_checkbox():
    """
    Valida contrato visual de flags booleanos de cuentas_contables.

    Imputable y monetaria se editan como checkbox HTML y se persisten como
    INTEGER 0/1 en SQLite.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/cuentas-contables/nueva/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="cc-imputable"' in html
    assert 'name="imputable"' in html
    assert 'data-field="imputable"' in html
    assert 'type="checkbox"' in html
    assert 'value="1"' in html
    assert 'id="cc-monetaria"' in html
    assert 'name="monetaria"' in html
    assert 'data-field="monetaria"' in html
    assert '<select\n                            id="cc-imputable"' not in html
    assert '<select\n                            id="cc-monetaria"' not in html
