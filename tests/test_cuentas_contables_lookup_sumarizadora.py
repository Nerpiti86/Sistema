from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _insertar_cuenta_contable_para_lookup_test(
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


def test_lookup_sumarizadora_devuelve_descripcion_de_cuenta_existente():
    """
    Valida endpoint JSON de lookup de sumarizadora.

    La route no ejecuta SQL directo: delega en service y devuelve la descripcion
    para que el JS complete descripcion_sumarizadora.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_cuenta_contable_para_lookup_test(
            db,
            "1.0.00.00.000",
            "ACTIVO",
        )

        response = client.get(
            "/contabilidad/cuentas-contables/lookup-sumarizadora/1.0.00.00.000/"
        )

    assert response.status_code == 200
    assert response.get_json() == {
        "encontrada": True,
        "cuenta": "1.0.00.00.000",
        "descripcion": "ACTIVO",
    }


def test_lookup_sumarizadora_inexistente_devuelve_404():
    """
    Valida lookup sin resultado.

    Si la cuenta sumarizadora no existe, la respuesta queda en 404 para que el
    JS marque error visual y bloquee submit.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get(
            "/contabilidad/cuentas-contables/lookup-sumarizadora/9.9.99.99.999/"
        )

    assert response.status_code == 404
    assert response.get_json() == {
        "encontrada": False,
        "cuenta": "9.9.99.99.999",
        "descripcion": "",
    }


def test_formulario_cuentas_contables_expone_lookup_de_sumarizadora():
    """
    Valida contrato HTML del lookup de sumarizadora.

    El template solo declara data-hooks y carga JS separado. Las cuentas raiz
    quedan sin resultado porque sumarizadora se renderiza vacia.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/cuentas-contables/nueva/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="cc-sumarizadora"' in html
    assert 'data-lookup="cuentas-contables-descripcion-sumarizadora"' in html
    assert "lookup-sumarizadora/__CUENTA_CONTABLE__/" in html
    assert 'id="cc-descripcion-sumarizadora"' in html
    assert 'data-lookup-result="cuentas-contables-descripcion-sumarizadora"' in html
    assert "js/cuentas_contables_form_lookup_sumarizadora.js" in html


def test_js_lookup_sumarizadora_tiene_nombres_identificables():
    """
    Valida que el JS separado no use nombres genericos.

    Las funciones y constantes deben dejar claro que pertenecen al lookup de
    descripcion de sumarizadora de cuentas_contables.
    """
    js = (
        "app/static/js/cuentas_contables_form_lookup_sumarizadora.js"
    )

    with open(js, encoding="utf-8") as archivo_js:
        contenido = archivo_js.read()

    assert "CUENTAS_CONTABLES_SELECTOR_LOOKUP_SUMARIZADORA" in contenido
    assert "CUENTAS_CONTABLES_SELECTOR_RESULTADO_LOOKUP_SUMARIZADORA" in contenido
    assert "buscarDescripcionSumarizadoraCuentaContable" in contenido
    assert "aplicarResultadoLookupSumarizadoraCuentaContable" in contenido
    assert "aplicarErrorLookupSumarizadoraCuentaContable" in contenido
    assert "limpiarLookupSumarizadoraCuentaContable" in contenido
    assert "inicializarLookupDescripcionSumarizadoraCuentaContable" in contenido
