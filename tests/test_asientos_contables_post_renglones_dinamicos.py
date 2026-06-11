from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.asientos_contables_service import (
    obtener_contexto_nuevo_asiento_contable_desde_formulario,
    preparar_asiento_contable_borrador_desde_formulario,
)


def _crear_app():
    """Crea app de test para validar renglones dinamicos de asientos."""
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
            "Ejercicio test renglones dinamicos",
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


def test_parser_formulario_acepta_indices_dinamicos_no_contiguos():
    """
    Valida parser de renglones dinamicos no contiguos.

    El JS puede reindexar, pero el backend debe tolerar indices presentes y
    ordenarlos por numero sin depender de una cantidad fija de renglones.
    """
    _, detalles_asiento = preparar_asiento_contable_borrador_desde_formulario(
        {
            "ejercicio_id": "7",
            "fecha": "10/06/2026",
            "descripcion": "Asiento dinamico",
            "detalles[0][cuenta_contable_codigo]": "1.1.01.01.997",
            "detalles[0][descripcion]": "Caja",
            "detalles[0][moneda_codigo]": "ARS",
            "detalles[0][cotizacion_1000000]": "1,000000",
            "detalles[0][debe_centavos]": "100,00",
            "detalles[2][cuenta_contable_codigo]": "1.1.01.01.998",
            "detalles[2][descripcion]": "Banco",
            "detalles[2][moneda_codigo]": "ARS",
            "detalles[2][cotizacion_1000000]": "1,000000",
            "detalles[2][debe_centavos]": "50,00",
            "detalles[5][cuenta_contable_codigo]": "4.1.01.01.999",
            "detalles[5][descripcion]": "Ingreso",
            "detalles[5][moneda_codigo]": "ARS",
            "detalles[5][cotizacion_1000000]": "1,000000",
            "detalles[5][haber_centavos]": "150,00",
        }
    )

    assert [detalle["cuenta_contable_codigo"] for detalle in detalles_asiento] == [
        "1.1.01.01.997",
        "1.1.01.01.998",
        "4.1.01.01.999",
    ]
    assert [detalle["debe_centavos"] for detalle in detalles_asiento] == [
        10000,
        5000,
        0,
    ]
    assert [detalle["haber_centavos"] for detalle in detalles_asiento] == [
        0,
        0,
        15000,
    ]


def test_contexto_error_preserva_renglones_dinamicos_del_formulario():
    """
    Valida re-render de formulario con renglones dinamicos.

    Si el POST falla, la pantalla debe poder reconstruir todos los renglones
    enviados y no volver artificialmente a los dos renglones base.
    """
    app = _crear_app()

    with app.app_context():
        apply_migrations()

        contexto = obtener_contexto_nuevo_asiento_contable_desde_formulario(
            {
                "ejercicio_id": "7",
                "fecha": "10/06/2026",
                "descripcion": "Re-render dinamico",
                "detalles[0][cuenta_contable_codigo]": "1.1.01.01.997",
                "detalles[0][debe_centavos]": "100,00",
                "detalles[1][cuenta_contable_codigo]": "1.1.01.01.998",
                "detalles[1][debe_centavos]": "50,00",
                "detalles[2][cuenta_contable_codigo]": "4.1.01.01.999",
                "detalles[2][haber_centavos]": "150,00",
            }
        )

    detalles_form = contexto["detalles_asiento_form"]

    assert len(detalles_form) == 3
    assert detalles_form[0]["cuenta_contable_codigo"] == "1.1.01.01.997"
    assert detalles_form[1]["cuenta_contable_codigo"] == "1.1.01.01.998"
    assert detalles_form[2]["cuenta_contable_codigo"] == "4.1.01.01.999"
    assert detalles_form[2]["haber_centavos"] == "150,00"


def test_post_nuevo_asiento_persiste_tres_renglones_dinamicos():
    """
    Valida POST real de nuevo asiento con renglones agregados por JS.

    El formulario envia detalles[0], detalles[1] y detalles[2]; la route debe
    crear un borrador balanceado y persistir tres renglones ordenados.
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
                "ejercicio_id": str(ejercicio_id),
                "fecha": "10/06/2026",
                "descripcion": "Asiento tres renglones",
                "tipo": "MANUAL",
                "estado": "BORRADOR",
                "moneda_origen_codigo": "ARS",
                "moneda_destino_codigo": "ARS",
                "cotizacion_tipo": "CIERRE",
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
                "detalles[2][haber_centavos]": "150,00",
            },
            follow_redirects=False,
        )

        asiento = db.execute(
            """
            SELECT id, estado, numero_asiento, descripcion
            FROM asientos_contables
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        detalles = db.execute(
            """
            SELECT
                renglon,
                cuenta_contable_codigo,
                debe_centavos,
                haber_centavos
            FROM asientos_contables_detalle
            WHERE asiento_id = ?
            ORDER BY renglon
            """,
            (asiento["id"],),
        ).fetchall()

    assert response.status_code == 302
    assert asiento["estado"] == "BORRADOR"
    assert asiento["numero_asiento"] is None
    assert asiento["descripcion"] == "Asiento tres renglones"
    assert [detalle["renglon"] for detalle in detalles] == [1, 2, 3]
    assert [detalle["cuenta_contable_codigo"] for detalle in detalles] == [
        cuenta_caja,
        cuenta_banco,
        cuenta_ingreso,
    ]
    assert sum(detalle["debe_centavos"] for detalle in detalles) == 15000
    assert sum(detalle["haber_centavos"] for detalle in detalles) == 15000
