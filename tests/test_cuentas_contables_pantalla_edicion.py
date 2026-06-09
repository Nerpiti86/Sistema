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
            sumarizadora
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            sumarizadora,
        ),
    )


def _insertar_jerarquia_caja_ars_para_test(db):
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.01.01.000",
        "CAJAS",
        imputable=0,
        monetaria=1,
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.01.01.001",
        "CAJA ARS",
        imputable=1,
        monetaria=1,
        sumarizadora="1.1.01.01.000",
    )


def test_pantalla_editar_cuenta_contable_responde_ok():
    """
    Valida formulario de edicion de cuentas_contables.

    La route no ejecuta SQL directo: obtiene contexto desde service y reutiliza
    el formulario con cuenta como identificador funcional de solo lectura.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        response = client.get(
            "/contabilidad/cuentas-contables/1.1.01.01.001/editar/"
        )

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Editar cuenta contable 1.1.01.01.001" in html
    assert 'id="cc-form"' in html
    assert 'id="cc-formulario"' in html
    assert 'data-action="editar_cuenta_contable"' in html
    assert 'id="cc-cuenta"' in html
    assert 'value="1.1.01.01.001"' in html
    assert "readonly" in html
    assert 'id="cc-descripcion-sumarizadora"' in html
    assert "/contabilidad/cuentas-contables/1.1.01.01.001/editar/" in html


def test_actualizar_cuenta_contable_desde_pantalla_redirige_a_listado():
    """
    Valida POST de edicion de cuentas_contables.

    La actualizacion conserva el codigo funcional de la URL y modifica solo
    campos mutables delegando normalizacion al service.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        response = client.post(
            "/contabilidad/cuentas-contables/1.1.01.01.001/editar/",
            data={
                "cuenta": "9.9.99.99.999",
                "descripcion": "CAJA PESOS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": "1",
                "sumarizadora": "",
            },
            follow_redirects=False,
        )

        cuenta_actualizada = db.execute(
            """
            SELECT cuenta, descripcion, imputable, monetaria, sumarizadora
            FROM cuentas_contables
            WHERE cuenta = ?
            LIMIT 1
            """,
            ("1.1.01.01.001",),
        ).fetchone()

    assert response.status_code == 302
    assert "/contabilidad/cuentas-contables/" in response.headers["Location"]
    assert cuenta_actualizada is not None
    assert cuenta_actualizada["cuenta"] == "1.1.01.01.001"
    assert cuenta_actualizada["descripcion"] == "CAJA PESOS"
    assert cuenta_actualizada["imputable"] == 1
    assert cuenta_actualizada["monetaria"] == 0
    assert cuenta_actualizada["sumarizadora"] is None


def test_actualizar_cuenta_contable_desde_pantalla_muestra_error_validacion():
    """
    Valida POST invalido de edicion con status 400.

    El error viene de service/repository; el template solo vuelve a mostrar el
    formulario con el codigo funcional de la URL.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        response = client.post(
            "/contabilidad/cuentas-contables/1.1.01.01.001/editar/",
            data={
                "cuenta": "1.1.01.01.001",
                "descripcion": "",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": "1",
                "monetaria": "1",
                "sumarizadora": "",
            },
        )

    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "Editar cuenta contable 1.1.01.01.001" in html
    assert "descripcion" in html


def test_pantalla_editar_cuenta_contable_inexistente_redirige_a_listado():
    """
    Valida edicion de cuenta inexistente.

    Si la cuenta no existe, la route informa el error y vuelve al listado.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get(
            "/contabilidad/cuentas-contables/9.9.99.99.999/editar/",
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert "/contabilidad/cuentas-contables/" in response.headers["Location"]


def test_listado_cuentas_contables_tiene_accion_editar():
    """
    Valida acceso de listado a edicion.

    Cada fila expone accion editar con data-row-codigo para trazabilidad del
    identificador funcional cuenta.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        response = client.get("/contabilidad/cuentas-contables/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-field="acciones"' in html
    assert 'id="cc-editar-1-1-01-01-001"' in html
    assert 'data-action="editar_cuenta_contable"' in html
    assert 'data-row-codigo="1.1.01.01.001"' in html
    assert "/contabilidad/cuentas-contables/1.1.01.01.001/editar/" in html


def test_formulario_edicion_cuenta_contable_carga_js_validacion_cuenta():
    """
    Valida que edicion reutiliza la validacion al vuelo de cuenta.

    Aunque la cuenta sea readonly en edicion, el formulario conserva el mismo
    contrato visual y el mismo archivo JS separado.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        response = client.get(
            "/contabilidad/cuentas-contables/1.1.01.01.001/editar/"
        )

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="cc-cuenta"' in html
    assert 'data-validation="cuentas-contables-formato-cuenta"' in html
    assert "readonly" in html
    assert "js/cuentas_contables_form_validacion_cuenta.js" in html


def test_actualizar_cuenta_contable_raiz_desde_pantalla_no_rechaza_formato():
    """
    Reproduce edicion de cuenta raiz 1.0.00.00.000.

    La cuenta raiz no tiene sumarizadora. El formato 1.0.00.00.000 debe ser
    aceptado tanto por la URL como por el formulario readonly.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_cuenta_contable_para_test(
            db,
            "1.0.00.00.000",
            "ACTIVO",
            saldo_habitual="DEBE",
            naturaleza="PATRIMONIAL",
            imputable=0,
            monetaria=0,
            sumarizadora=None,
        )

        response = client.post(
            "/contabilidad/cuentas-contables/1.0.00.00.000/editar/",
            data={
                "cuenta": "1.0.00.00.000",
                "descripcion": "ACTIVO",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "sumarizadora": "",
            },
            follow_redirects=False,
        )

        cuenta_actualizada = db.execute(
            """
            SELECT cuenta, descripcion, imputable, monetaria, sumarizadora
            FROM cuentas_contables
            WHERE cuenta = ?
            LIMIT 1
            """,
            ("1.0.00.00.000",),
        ).fetchone()

    html = response.get_data(as_text=True)

    assert response.status_code == 302, html
    assert cuenta_actualizada is not None
    assert cuenta_actualizada["cuenta"] == "1.0.00.00.000"
    assert cuenta_actualizada["descripcion"] == "ACTIVO"
    assert cuenta_actualizada["imputable"] == 0
    assert cuenta_actualizada["monetaria"] == 0
    assert cuenta_actualizada["sumarizadora"] is None
