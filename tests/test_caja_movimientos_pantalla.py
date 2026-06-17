import re
from pathlib import Path

from app import create_app
from app.caja.movimientos_caja_repository import crear_movimiento_caja
from app.config import TestConfig
from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_automatico_confirmado,
)
from app.db import apply_migrations, get_db


def _insertar_ejercicio_contable_caja(db) -> int:
    db.execute(
        """
        INSERT INTO ejercicios_contables (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            fase_cierre,
            bloqueado,
            es_primer_ejercicio,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            "ABIERTO",
            1,
            "ABIERTO",
            0,
            1,
            "2026-01-01 10:00:00",
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def _insertar_cuenta_contable_caja(db, cuenta: str, descripcion: str) -> str:
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
            "2026-01-01 10:00:00",
        ),
    )

    return cuenta


def _insertar_medio_operativo_caja(db, cuenta_caja: str) -> None:
    db.execute(
        """
        INSERT INTO medios_operativos (
            codigo,
            nombre,
            tipo,
            cuenta_contable_codigo,
            moneda_codigo,
            activo,
            orden,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "CAJA_TEST",
            "Caja pantalla",
            "EFECTIVO",
            cuenta_caja,
            "ARS",
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )


def _crear_movimiento_caja_confirmado_para_pantalla():
    db = get_db()
    ejercicio_id = _insertar_ejercicio_contable_caja(db)
    cuenta_caja = _insertar_cuenta_contable_caja(
        db,
        "1.1.01.01.991",
        "Caja prueba pantalla",
    )
    cuenta_haber = _insertar_cuenta_contable_caja(
        db,
        "4.1.01.01.991",
        "Cuenta contrapartida pantalla",
    )
    _insertar_medio_operativo_caja(db, cuenta_caja)

    asiento = crear_asiento_contable_automatico_confirmado(
        {
            "ejercicio_id": ejercicio_id,
            "fecha": "2026-06-17",
            "descripcion": "Cobranza caja pantalla",
            "tipo": "COBRANZA",
        },
        [
            {
                "cuenta_contable_codigo": cuenta_caja,
                "descripcion": "Debe caja pantalla",
                "nominal_debe_centavos": 123456,
                "debe_centavos": 123456,
            },
            {
                "cuenta_contable_codigo": cuenta_haber,
                "descripcion": "Haber cobranza pantalla",
                "nominal_haber_centavos": 123456,
                "haber_centavos": 123456,
            },
        ],
    )

    movimiento = crear_movimiento_caja(
        {
            "fecha": "2026-06-17",
            "tipo_movimiento": "INGRESO",
            "origen_tipo": "CLIENTE_COBRANZA",
            "origen_id": 7,
            "moneda_contable_codigo": "ARS",
            "total_contable_centavos": 123456,
            "estado": "CONFIRMADO",
            "asiento_id": asiento["id"],
            "observaciones": "Cobranza caja pantalla",
        },
        [
            {
                "medio_operativo_codigo": "CAJA_TEST",
                "cuenta_contable_codigo": cuenta_caja,
                "moneda_codigo": "ARS",
                "fecha_valor": "2026-06-18",
                "referencia": "REC-C-0001",
                "importe_nominal_centavos": 123456,
                "cotizacion_1000000": 1000000,
                "importe_contable_centavos": 123456,
                "detalle": "Pago efectivo pantalla",
                "orden": 1,
            }
        ],
    )

    return movimiento, asiento


def test_listado_movimientos_caja_responde_ok_sin_datos():
    """Valida pantalla mínima de listado de movimientos de caja."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/caja/movimientos/")

    assert response.status_code == 200
    assert b"Movimientos de caja" in response.data
    assert b'id="mc-listado"' in response.data
    assert b'id="mc-tabla"' in response.data
    assert b'data-table="movimientos_caja"' in response.data
    assert b'data-query="listar_movimientos_caja"' in response.data
    assert b"No hay movimientos de caja cargados." in response.data


def test_listado_movimientos_caja_muestra_movimiento_confirmado():
    """Valida listado con fecha e importes formateados para pantalla."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        movimiento, asiento = _crear_movimiento_caja_confirmado_para_pantalla()
        response = client.get("/caja/movimientos/")

    assert response.status_code == 200
    assert f'id="mc-row-{movimiento["id"]}"'.encode() in response.data
    assert f'data-row-id="{movimiento["id"]}"'.encode() in response.data
    assert b"17/06/2026" in response.data
    assert b"2026-06-17" not in response.data
    assert b"INGRESO" in response.data
    assert b"CLIENTE_COBRANZA #7" in response.data
    assert b"1.234,56" in response.data
    assert b"Confirmado" in response.data
    assert f"/caja/movimientos/{movimiento['id']}/".encode() in response.data
    assert f"/contabilidad/asientos-contables/{asiento['id']}/".encode() in response.data

    html = response.data.decode("utf-8")
    assert re.search(r">\s*123456\s*<", html) is None


def test_detalle_movimiento_caja_muestra_cabecera_y_lineas():
    """Valida detalle solo lectura de movimiento de caja con líneas."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        movimiento, asiento = _crear_movimiento_caja_confirmado_para_pantalla()
        response = client.get(f"/caja/movimientos/{movimiento['id']}/")

    assert response.status_code == 200
    assert b"Detalle movimiento de caja" in response.data
    assert b'id="mc-detalle"' in response.data
    assert f'data-row-id="{movimiento["id"]}"'.encode() in response.data
    assert b'id="mc-detalle-tabla"' in response.data
    assert b'id="mc-detalle-cantidad-lineas"' in response.data
    assert b"17/06/2026" in response.data
    assert b"18/06/2026" in response.data
    assert b"2026-06-17" not in response.data
    assert b"2026-06-18" not in response.data
    assert b"INGRESO" in response.data
    assert b"CLIENTE_COBRANZA #7" in response.data
    assert b"Caja pantalla" in response.data
    assert b"CAJA_TEST" in response.data
    assert b"1.1.01.01.991" in response.data
    assert b"Caja prueba pantalla" in response.data
    assert b"REC-C-0001" in response.data
    assert b"Pago efectivo pantalla" in response.data
    assert b"1.234,56" in response.data
    assert b"1,000000" in response.data
    assert f"/contabilidad/asientos-contables/{asiento['id']}/".encode() in response.data

    html = response.data.decode("utf-8")
    assert re.search(r">\s*123456\s*<", html) is None


def test_detalle_movimiento_caja_no_expone_edicion_ni_anulacion():
    """Contrato: el detalle de caja de este corte es solo lectura."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        movimiento, _asiento = _crear_movimiento_caja_confirmado_para_pantalla()
        response = client.get(f"/caja/movimientos/{movimiento['id']}/")

    assert response.status_code == 200
    assert b"Editar" not in response.data
    assert b"Anular" not in response.data
    assert b'method="post"' not in response.data


def test_detalle_movimiento_caja_inexistente_redirige_al_listado():
    """Valida manejo de movimiento inexistente sin error técnico."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/caja/movimientos/999999/")

    assert response.status_code == 302
    assert "/caja/movimientos/" in response.headers["Location"]


def test_routes_y_service_caja_respetan_capas_sin_sql_directo():
    """Routes y service de caja no deben usar SQL ni get_db directo."""
    routes = Path("app/caja/routes.py").read_text(encoding="utf-8")
    service = Path("app/caja/movimientos_caja_service.py").read_text(encoding="utf-8")

    assert "get_db" not in routes
    assert ".execute(" not in routes
    assert "get_db" not in service
    assert ".execute(" not in service


def test_movimientos_caja_form_js_no_mantiene_alert_wip():
    """El asset relacionado de caja no debe mostrar mensaje WIP obsoleto."""
    contenido = Path("app/static/js/movimientos_caja_form.js").read_text(
        encoding="utf-8"
    )

    assert "WIP" not in contenido
    assert "persistencia pendiente" not in contenido
