from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_pantalla_tablas_comunes_medios_operativos_responde_ok():
    """
    Valida pantalla de medios operativos bajo Tablas Comunes.

    La route usa service y el template mantiene IDs cortos y data-* para
    trazabilidad tecnica de tabla, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/medios-operativos/")

    assert response.status_code == 200
    assert b"Medios operativos" in response.data
    assert b'id="mope-listado"' in response.data
    assert b'id="mope-tabla"' in response.data
    assert b'data-table="medios_operativos"' in response.data
    assert b"Nuevo medio" in response.data
    assert b"No hay medios operativos cargados." in response.data


def test_navbar_tiene_tablas_comunes_medios_operativos():
    """Valida acceso de navegacion Tablas Comunes > Medios operativos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/medios-operativos/")

    assert response.status_code == 200
    assert b"Tablas comunes" in response.data
    assert b"/tablas-comunes/medios-operativos/" in response.data
    assert b'id="ns-nav-tablas-comunes"' in response.data
    assert b'id="ns-nav-medios-operativos"' in response.data


def test_formulario_nuevo_medio_operativo_responde_ok():
    """Valida formulario de alta manual de medios operativos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/tablas-comunes/medios-operativos/nuevo/")

    assert response.status_code == 200
    assert b"Nuevo medio operativo" in response.data
    assert b'id="mope-form"' in response.data
    assert b'id="mope-codigo"' in response.data
    assert b'id="mope-cuenta-contable"' in response.data


def test_formulario_medio_operativo_respeta_orden_visual():
    """
    Valida el orden visual del formulario de medios operativos.

    La pantalla debe leerse por bloques: identificacion, moneda/cambio,
    cuenta contable, datos bancarios y estado operativo.
    """
    contenido = Path(
        "app/tablas_comunes/templates/tablas_comunes/medios_operativos_form.html"
    ).read_text(encoding="utf-8")
    ids = [
        'id="mope-codigo"',
        'id="mope-nombre"',
        'id="mope-tipo"',
        'id="mope-moneda"',
        'id="mope-requiere-cotizacion"',
        'id="mope-cotizacion"',
        'id="mope-cuenta-contable"',
        'id="mope-banco"',
        'id="mope-plaza"',
        'id="mope-sucursal"',
        'id="mope-numero-cuenta"',
        'id="mope-cuit"',
        'id="mope-orden"',
        'id="mope-activo"',
    ]

    posiciones = [contenido.index(item) for item in ids]

    assert posiciones == sorted(posiciones)


def test_crear_medio_operativo_desde_pantalla():
    """Valida POST de alta manual sin SQL en route."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        response = client.post(
            "/tablas-comunes/medios-operativos/nuevo/",
            data={
                "codigo": "1",
                "nombre": "Caja pesos pantalla",
                "tipo": "EFECTIVO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "1.1.01.01.001",
                "activo": "1",
                "orden": "10",
            },
            follow_redirects=True,
        )
        medio = get_db().execute(
            "SELECT codigo, nombre FROM medios_operativos WHERE codigo = ?",
            ("1",),
        ).fetchone()

    assert response.status_code == 200
    assert medio["codigo"] == "1"
    assert medio["nombre"] == "Caja pesos pantalla"
    assert b"Caja pesos pantalla" in response.data


def test_editar_medio_operativo_desde_pantalla():
    """Valida GET y POST de edicion manual de medio operativo."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        _insertar_medio_prueba()
        get_response = client.get("/tablas-comunes/medios-operativos/1/editar/")
        post_response = client.post(
            "/tablas-comunes/medios-operativos/1/editar/",
            data={
                "nombre": "Caja pesos editada",
                "tipo": "EFECTIVO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "1.1.01.01.001",
                "activo": "1",
                "orden": "15",
            },
            follow_redirects=True,
        )
        medio = get_db().execute(
            "SELECT codigo, nombre, orden FROM medios_operativos WHERE codigo = ?",
            ("1",),
        ).fetchone()

    assert get_response.status_code == 200
    assert b"Editar medio operativo 1 - Caja pesos" in get_response.data
    assert post_response.status_code == 200
    assert medio["nombre"] == "Caja pesos editada"
    assert medio["orden"] == 15


def test_editar_medio_operativo_con_error_mantiene_titulo_codigo_nombre():
    """
    Valida titulo de edicion ante error de formulario.

    Si el POST invalido vuelve al formulario, el encabezado debe conservar
    codigo y nombre para ubicar claramente el medio operativo editado.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        _insertar_medio_prueba()
        response = client.post(
            "/tablas-comunes/medios-operativos/1/editar/",
            data={
                "nombre": "Caja pesos",
                "tipo": "EFECTIVO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "",
                "activo": "1",
                "orden": "15",
            },
            follow_redirects=False,
        )

    assert response.status_code == 400
    assert b"Editar medio operativo 1 - Caja pesos" in response.data


def test_activar_desactivar_medio_operativo_desde_pantalla():
    """Valida POST de baja logica y reactivacion desde listado."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        _insertar_medio_prueba()
        desactivar_response = client.post(
            "/tablas-comunes/medios-operativos/1/desactivar/",
            follow_redirects=True,
        )
        medio_desactivado = get_db().execute(
            "SELECT activo FROM medios_operativos WHERE codigo = ?",
            ("1",),
        ).fetchone()
        activar_response = client.post(
            "/tablas-comunes/medios-operativos/1/activar/",
            follow_redirects=True,
        )
        medio_activado = get_db().execute(
            "SELECT activo FROM medios_operativos WHERE codigo = ?",
            ("1",),
        ).fetchone()

    assert desactivar_response.status_code == 200
    assert activar_response.status_code == 200
    assert medio_desactivado["activo"] == 0
    assert medio_activado["activo"] == 1


def _insertar_cuenta_prueba():
    get_db().execute(
        """
        INSERT INTO cuentas_contables (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "1.1.01.01.001",
            "Caja ARS",
            "DEBE",
            "PATRIMONIAL",
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )


def _insertar_medio_prueba():
    get_db().execute(
        """
        INSERT INTO medios_operativos (
            codigo,
            nombre,
            tipo,
            requiere_cotizacion,
            cotizacion_default_centavos,
            cuenta_contable_codigo,
            moneda_codigo,
            activo,
            orden,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "1",
            "Caja pesos",
            "EFECTIVO",
            0,
            None,
            "1.1.01.01.001",
            "ARS",
            1,
            10,
            "2026-01-01 10:00:00",
        ),
    )


def test_formulario_medio_operativo_no_usa_js_inline():
    """
    Contrato: el formulario de medios operativos solo declara hooks HTML.

    El comportamiento de pantalla debe vivir en asset estatico JS, no en un
    bloque script pegado dentro del template.
    """
    contenido = Path(
        "app/tablas_comunes/templates/tablas_comunes/medios_operativos_form.html"
    ).read_text(encoding="utf-8")

    assert "<script>" not in contenido
    assert "js/medios_operativos_form.js" in contenido


def test_formulario_medio_operativo_declara_url_lookup_por_data_attribute():
    """
    Contrato: las URLs Flask se generan en template con url_for.

    El JS debe leerlas desde data-* para evitar endpoints hardcodeados dentro
    del asset estatico.
    """
    contenido = Path(
        "app/tablas_comunes/templates/tablas_comunes/medios_operativos_form.html"
    ).read_text(encoding="utf-8")

    assert "data-cuentas-imputables-url=" in contenido
    assert "contabilidad.buscar_cuentas_contables_imputables_json" in contenido
    assert "data-cuentas-imputables-limite=\"10\"" in contenido


def test_js_medios_operativos_form_respeta_contrato_asset_estatico():
    """
    Contrato: el JS especifico de medios operativos vive en app/static/js.

    Debe tomar el endpoint desde dataset, usar fetch JSON y no contener rutas
    Flask hardcodeadas.
    """
    contenido = Path("app/static/js/medios_operativos_form.js").read_text(
        encoding="utf-8"
    )

    assert "dataset.cuentasImputablesUrl" in contenido
    assert "dataset.cuentasImputablesLimite" in contenido
    assert "new URL(" in contenido
    assert "fetch(" in contenido
    assert "/contabilidad/cuentas-contables/imputables/buscar/" not in contenido

