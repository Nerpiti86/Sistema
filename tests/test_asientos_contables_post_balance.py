from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _crear_app():
    """Crea app de test para validar balance del POST de asientos."""
    return create_app(TestConfig)


def _crear_ejercicio_activo(db) -> int:
    db.execute(
        """
        INSERT INTO ejercicios_contables (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            creado_en,
            fase_cierre,
            bloqueado,
            es_primer_ejercicio
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "2026",
            "Ejercicio test balance post",
            "2026-01-01",
            "2026-12-31",
            "ABIERTO",
            1,
            "2026-01-01 00:00:00",
            "ABIERTO",
            0,
            1,
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def _crear_cuenta_imputable(db, cuenta: str, descripcion: str) -> str:
    db.execute(
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
            cuenta,
            descripcion,
            "DEBE",
            "PATRIMONIAL",
            1,
            1,
            "2026-01-01 00:00:00",
        ),
    )

    return cuenta


def _datos_base_post(ejercicio_id: int) -> dict[str, str]:
    return {
        "ejercicio_id": str(ejercicio_id),
        "fecha": "10/06/2026",
        "descripcion": "Asiento desbalanceado",
        "tipo": "MANUAL",
        "estado": "BORRADOR",
        "moneda_origen_codigo": "ARS",
        "moneda_destino_codigo": "ARS",
        "cotizacion_tipo": "CIERRE",
    }


def _cantidad_asientos(db) -> int:
    return int(
        db.execute("SELECT COUNT(*) AS cantidad FROM asientos_contables").fetchone()[
            "cantidad"
        ]
    )


def _cantidad_detalles(db) -> int:
    return int(
        db.execute(
            "SELECT COUNT(*) AS cantidad FROM asientos_contables_detalle"
        ).fetchone()["cantidad"]
    )


def test_post_nuevo_asiento_desbalanceado_devuelve_400_y_no_persiste():
    """
    Valida rechazo de POST desbalanceado.

    La route debe devolver 400, mostrar el error de balance y no persistir ni
    cabecera ni detalle.
    """
    app = _crear_app()
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio_activo(db)
        cuenta_debe = _crear_cuenta_imputable(db, "1.1.01.01.997", "Caja test")
        cuenta_haber = _crear_cuenta_imputable(
            db,
            "4.1.01.01.999",
            "Ingreso test",
        )

        response = client.post(
            "/contabilidad/asientos-contables/nuevo/",
            data={
                **_datos_base_post(ejercicio_id),
                "detalles[0][cuenta_contable_codigo]": cuenta_debe,
                "detalles[0][descripcion]": "",
                "detalles[0][moneda_codigo]": "ARS",
                "detalles[0][cotizacion_1000000]": "1,000000",
                "detalles[0][debe_centavos]": "100,00",
                "detalles[0][haber_centavos]": "",
                "detalles[1][cuenta_contable_codigo]": cuenta_haber,
                "detalles[1][descripcion]": "",
                "detalles[1][moneda_codigo]": "ARS",
                "detalles[1][cotizacion_1000000]": "1,000000",
                "detalles[1][debe_centavos]": "",
                "detalles[1][haber_centavos]": "90,00",
            },
            follow_redirects=False,
        )

        cantidad_asientos = _cantidad_asientos(db)
        cantidad_detalles = _cantidad_detalles(db)

    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "El asiento contable no balancea." in html
    assert cantidad_asientos == 0
    assert cantidad_detalles == 0


def test_post_nuevo_asiento_desbalanceado_preserva_tres_renglones():
    """
    Valida re-render de POST desbalanceado con renglones dinamicos.

    Si el usuario agrego un tercer renglon y el asiento no balancea, la pantalla
    debe volver con los tres renglones y sus nombres detalles[n][...].
    """
    app = _crear_app()
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio_activo(db)
        cuenta_caja = _crear_cuenta_imputable(db, "1.1.01.01.997", "Caja test")
        cuenta_banco = _crear_cuenta_imputable(db, "1.1.01.01.998", "Banco test")
        cuenta_ingreso = _crear_cuenta_imputable(
            db,
            "4.1.01.01.999",
            "Ingreso test",
        )

        response = client.post(
            "/contabilidad/asientos-contables/nuevo/",
            data={
                **_datos_base_post(ejercicio_id),
                "detalles[0][cuenta_contable_codigo]": cuenta_caja,
                "detalles[0][descripcion]": "",
                "detalles[0][moneda_codigo]": "ARS",
                "detalles[0][cotizacion_1000000]": "1,000000",
                "detalles[0][debe_centavos]": "100,00",
                "detalles[0][haber_centavos]": "",
                "detalles[1][cuenta_contable_codigo]": cuenta_banco,
                "detalles[1][descripcion]": "",
                "detalles[1][moneda_codigo]": "ARS",
                "detalles[1][cotizacion_1000000]": "1,000000",
                "detalles[1][debe_centavos]": "50,00",
                "detalles[1][haber_centavos]": "",
                "detalles[2][cuenta_contable_codigo]": cuenta_ingreso,
                "detalles[2][descripcion]": "",
                "detalles[2][moneda_codigo]": "ARS",
                "detalles[2][cotizacion_1000000]": "1,000000",
                "detalles[2][debe_centavos]": "",
                "detalles[2][haber_centavos]": "140,00",
            },
            follow_redirects=False,
        )

        cantidad_asientos = _cantidad_asientos(db)
        cantidad_detalles = _cantidad_detalles(db)

    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "El asiento contable no balancea." in html
    assert cantidad_asientos == 0
    assert cantidad_detalles == 0
    assert 'id="as-det-row-2"' in html
    assert 'name="detalles[2][cuenta_contable_codigo]"' in html
    assert 'name="detalles[2][haber_centavos]"' in html
    assert 'value="140,00"' in html
    assert 'id="as-renglones-cantidad"' in html


def test_post_nuevo_asiento_con_importes_cero_no_persiste():
    """
    Valida rechazo de asiento sin importes efectivos.

    La pantalla no debe crear un borrador si los renglones enviados no tienen
    debe ni haber.
    """
    app = _crear_app()
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio_activo(db)
        cuenta_debe = _crear_cuenta_imputable(db, "1.1.01.01.997", "Caja test")
        cuenta_haber = _crear_cuenta_imputable(
            db,
            "4.1.01.01.999",
            "Ingreso test",
        )

        response = client.post(
            "/contabilidad/asientos-contables/nuevo/",
            data={
                **_datos_base_post(ejercicio_id),
                "detalles[0][cuenta_contable_codigo]": cuenta_debe,
                "detalles[0][descripcion]": "",
                "detalles[0][moneda_codigo]": "ARS",
                "detalles[0][cotizacion_1000000]": "1,000000",
                "detalles[0][debe_centavos]": "",
                "detalles[0][haber_centavos]": "",
                "detalles[1][cuenta_contable_codigo]": cuenta_haber,
                "detalles[1][descripcion]": "",
                "detalles[1][moneda_codigo]": "ARS",
                "detalles[1][cotizacion_1000000]": "1,000000",
                "detalles[1][debe_centavos]": "",
                "detalles[1][haber_centavos]": "",
            },
            follow_redirects=False,
        )

        cantidad_asientos = _cantidad_asientos(db)
        cantidad_detalles = _cantidad_detalles(db)

    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "Cada renglon debe tener importe." in html
    assert cantidad_asientos == 0
    assert cantidad_detalles == 0
