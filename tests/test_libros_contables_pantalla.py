import re

from app import create_app
from app.config import TestConfig
from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_automatico_confirmado,
)
from app.db import apply_migrations, get_db


CUENTA_DEUDORES = "1.1.03.01.995"
CUENTA_INGRESOS = "4.1.01.01.995"


def _insertar_ejercicio_libro_diario(db) -> int:
    cursor = db.execute(
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
            "Ejercicio Libro Diario",
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
    return int(cursor.lastrowid)


def _insertar_cuenta_libro_diario(
    db,
    cuenta: str,
    descripcion: str,
    saldo_habitual: str,
) -> str:
    db.execute(
        """
        INSERT OR IGNORE INTO cuentas_contables (
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
            saldo_habitual,
            "PATRIMONIAL" if saldo_habitual == "DEBE" else "RESULTADO",
            1,
            1 if saldo_habitual == "DEBE" else 0,
            "2026-01-01 10:00:00",
        ),
    )
    db.execute(
        """
        UPDATE cuentas_contables
        SET descripcion = ?,
            saldo_habitual = ?
        WHERE cuenta = ?
        """,
        (descripcion, saldo_habitual, cuenta),
    )
    return cuenta


def _crear_asiento_libro_diario(db) -> dict:
    ejercicio_id = _insertar_ejercicio_libro_diario(db)
    cuenta_debe = _insertar_cuenta_libro_diario(
        db,
        CUENTA_DEUDORES,
        "Deudores por ventas pantalla LD",
        "DEBE",
    )
    cuenta_haber = _insertar_cuenta_libro_diario(
        db,
        CUENTA_INGRESOS,
        "Ingresos por servicios pantalla LD",
        "HABER",
    )

    return crear_asiento_contable_automatico_confirmado(
        {
            "ejercicio_id": ejercicio_id,
            "fecha": "2026-06-10",
            "descripcion": (
                "Comprobante: FC C 0001-00000001 | "
                "Sujeto: Nerpiti Nicolas Neri"
            ),
            "tipo": "VENTA",
        },
        [
            {
                "cuenta_contable_codigo": cuenta_debe,
                "descripcion": "Linea deudores pantalla",
                "nominal_debe_centavos": 3500000,
                "debe_centavos": 3500000,
            },
            {
                "cuenta_contable_codigo": cuenta_haber,
                "descripcion": "Linea ingresos pantalla",
                "nominal_haber_centavos": 3500000,
                "haber_centavos": 3500000,
            },
        ],
    )


def test_pantalla_libro_diario_responde_ok_sin_movimientos():
    """Valida pantalla inicial del Libro Diario con ejercicio activo sin movimientos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_libro_diario(db)

        response = client.get("/contabilidad/libros/diario/")

    assert response.status_code == 200
    assert b"Libro diario" in response.data
    assert b"No hay movimientos para el Libro Diario." in response.data
    assert b'id="ld-listado"' in response.data
    assert b'id="ld-filtros"' in response.data
    assert b'id="ld-resumen"' in response.data
    assert b'id="ld-mensaje-sin-datos"' in response.data
    assert b'data-table="asientos_contables"' in response.data
    assert b'data-query="obtener_contexto_pantalla_libro_diario"' in response.data


def test_pantalla_libro_diario_muestra_asiento_comprobante_sujeto_y_totales():
    """
    Valida la pantalla con asiento confirmado.

    La vista muestra número, fecha, comprobante, sujeto, cuenta, nombre de
    cuenta, debe, haber y totales con formato argentino.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        asiento = _crear_asiento_libro_diario(db)

        response = client.get("/contabilidad/libros/diario/")

    assert response.status_code == 200
    assert b"EJ2026-0000001" in response.data
    assert b"10/06/2026" in response.data
    assert b"FC C 0001-00000001" in response.data
    assert b"Nerpiti Nicolas Neri" in response.data
    assert CUENTA_DEUDORES.encode() in response.data
    assert b"Deudores por ventas pantalla LD" in response.data
    assert CUENTA_INGRESOS.encode() in response.data
    assert b"Ingresos por servicios pantalla LD" in response.data
    assert b"35.000,00" in response.data
    assert b"id=\"ld-total-debe\"" in response.data
    assert b"id=\"ld-total-haber\"" in response.data
    assert b"id=\"ld-diferencia\"" in response.data
    assert f'id="ld-asiento-{asiento["id"]}"'.encode() in response.data
    assert f'data-row-id="{asiento["id"]}"'.encode() in response.data

    html = response.data.decode("utf-8")
    assert re.search(r">\\s*3500000\\s*<", html) is None


def test_pantalla_contabilidad_tiene_acceso_a_libro_diario():
    """Valida acceso desde el índice de Contabilidad."""
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Libro diario" in response.data
    assert b"/contabilidad/libros/diario/" in response.data
    assert b'id="ld-acceso"' in response.data
    assert b'data-table="asientos_contables"' in response.data
    assert b'data-action="ver_libro_diario"' in response.data





def test_pantalla_libro_diario_ui_ux_sin_repeticiones_y_totales_destacados():
    """
    Valida ajuste UI/UX del Libro Diario.

    La card no repite "Asiento EJ..." arriba, pero mantiene dentro los cuatro
    datos principales: numero de asiento, fecha, comprobante y sujeto.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_asiento_libro_diario(db)

        response = client.get("/contabilidad/libros/diario/")

    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert "Asiento EJ2026-0000001" not in html
    assert "Asiento contable" in html

    assert "Número de asiento" in html
    assert "Fecha" in html
    assert "Comprobante" in html
    assert "Sujeto" in html

    assert 'id="ld-asiento-numero-' in html
    assert 'id="ld-asiento-fecha-' in html
    assert 'id="ld-asiento-comprobante-' in html
    assert 'id="ld-asiento-sujeto-' in html

    assert "FC C 0001-00000001" in html
    assert "Nerpiti Nicolas Neri" in html

    assert "data-ui-control=\"date\"" in html
    assert "data-ui-control=\"select\"" in html
    assert "form-control form-control-sm" in html
    assert "form-select form-select-sm" in html
    assert "btn btn-primary btn-sm" in html
    assert "table-light border-top border-2" in html
