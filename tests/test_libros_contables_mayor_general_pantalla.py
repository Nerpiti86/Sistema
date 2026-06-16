import re
from urllib.parse import urlencode

from app import create_app
from app.config import TestConfig
from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_automatico_confirmado,
)
from app.db import apply_migrations, get_db


CUENTA_DEBE = "1.1.03.01.992"
CUENTA_HABER = "4.1.01.01.992"


def _insertar_ejercicio_mayor_general(db) -> int:
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
            "Ejercicio Mayor General",
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


def _insertar_cuenta_mayor_general(
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


def _crear_asiento_mayor_general(
    ejercicio_id: int,
    *,
    fecha: str,
    descripcion: str,
    importe_centavos: int,
) -> dict:
    return crear_asiento_contable_automatico_confirmado(
        {
            "ejercicio_id": ejercicio_id,
            "fecha": fecha,
            "descripcion": descripcion,
            "tipo": "VENTA",
        },
        [
            {
                "cuenta_contable_codigo": CUENTA_DEBE,
                "descripcion": "Linea debe mayor general",
                "nominal_debe_centavos": importe_centavos,
                "debe_centavos": importe_centavos,
            },
            {
                "cuenta_contable_codigo": CUENTA_HABER,
                "descripcion": "Linea haber mayor general",
                "nominal_haber_centavos": importe_centavos,
                "haber_centavos": importe_centavos,
            },
        ],
    )


def _crear_datos_mayor_general(db) -> int:
    ejercicio_id = _insertar_ejercicio_mayor_general(db)
    _insertar_cuenta_mayor_general(
        db,
        CUENTA_DEBE,
        "Deudores por ventas pantalla mayor general",
        "DEBE",
    )
    _insertar_cuenta_mayor_general(
        db,
        CUENTA_HABER,
        "Ingresos por servicios pantalla mayor general",
        "HABER",
    )

    _crear_asiento_mayor_general(
        ejercicio_id,
        fecha="2026-05-31",
        descripcion="Comprobante: SI | Sujeto: Inicial",
        importe_centavos=1000000,
    )
    _crear_asiento_mayor_general(
        ejercicio_id,
        fecha="2026-06-10",
        descripcion="Comprobante: FC C 0001-00000001 | Sujeto: Cliente mayor general",
        importe_centavos=3500000,
    )

    return ejercicio_id


def test_pantalla_mayor_general_responde_ok_sin_saldos():
    """Valida pantalla inicial del Mayor General sin saldos."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_mayor_general(db)

        response = client.get("/contabilidad/libros/mayor-general/")

    assert response.status_code == 200
    assert b"Libro mayor general" in response.data
    assert b"No hay saldos para el Libro Mayor General." in response.data
    assert b'id="lmg-listado"' in response.data
    assert b'id="lmg-filtros"' in response.data
    assert b'id="lmg-resumen"' not in response.data
    assert b'id="lmg-tabla"' in response.data
    assert b'id="lmg-mensaje-sin-datos"' in response.data
    assert b'data-query="obtener_contexto_pantalla_mayor_general"' in response.data


def test_pantalla_mayor_general_muestra_saldos_por_cuenta():
    """Valida Mayor General con saldo inicial, totales y saldo final."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_datos_mayor_general(db)

        query = urlencode(
            {
                "fecha_desde": "2026-06-01",
                "fecha_hasta": "2026-06-30",
            }
        )
        response = client.get(f"/contabilidad/libros/mayor-general/?{query}")

    assert response.status_code == 200
    assert b"Libro mayor general" in response.data
    assert b"Deudores por ventas pantalla mayor general" in response.data
    assert b"Ingresos por servicios pantalla mayor general" in response.data
    assert CUENTA_DEBE.encode() in response.data
    assert CUENTA_HABER.encode() in response.data
    assert b"DEBE" in response.data
    assert b"HABER" in response.data

    assert b"10.000,00" in response.data
    assert b"35.000,00" in response.data
    assert b"45.000,00" in response.data
    assert b"0,00" in response.data
    assert b'id="lmg-resumen"' not in response.data
    assert b'id="lmg-total-saldo-final"' not in response.data
    assert b'id="lmg-diferencia-periodo"' not in response.data
    assert b'data-field="saldo_inicial_centavos"' in response.data
    assert b'data-field="total_debe_periodo_centavos"' in response.data
    assert b'data-field="total_haber_periodo_centavos"' in response.data
    assert b'data-field="saldo_final_centavos"' in response.data

    html = response.data.decode("utf-8")
    assert re.search(r">\s*3500000\s*<", html) is None
    assert re.search(r">\s*4500000\s*<", html) is None


def test_pantalla_contabilidad_tiene_acceso_a_mayor_general():
    """Valida acceso desde el índice de Contabilidad."""
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Libro mayor general" in response.data
    assert b"/contabilidad/libros/mayor-general/" in response.data
    assert b'id="lmg-acceso"' in response.data
    assert b'data-table="asientos_contables_detalle"' in response.data
    assert b'data-action="ver_mayor_general"' in response.data


def test_pantalla_mayor_general_filtros_usan_contrato_ui():
    """
    Valida contrato UI de filtros del Mayor General.

    Las fechas usan calendario argentino, el select usa NeriSoft Select y los
    controles conservan tamaño normal.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_datos_mayor_general(db)

        query = urlencode(
            {
                "fecha_desde": "01/06/2026",
                "fecha_hasta": "30/06/2026",
                "estado": "CONFIRMADO",
            }
        )
        response = client.get(f"/contabilidad/libros/mayor-general/?{query}")

    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'id="lmg-fecha-desde"' in html
    assert 'id="lmg-fecha-hasta"' in html
    assert 'id="lmg-estado"' in html
    assert 'id="lmg-aplicar-filtros"' in html

    assert 'data-datepicker="fecha-argentina"' in html
    assert 'data-ns-select' in html
    assert 'data-ns-select-placeholder="Seleccionar estado"' in html

    assert 'type="text"' in html
    assert 'inputmode="numeric"' in html
    assert 'placeholder="DD/MM/AAAA"' in html
    assert 'value="01/06/2026"' in html
    assert 'value="30/06/2026"' in html

    assert 'type="date"' not in html
    assert 'data-ui-control="date"' not in html
    assert 'data-ui-control="select"' not in html

    assert 'class="form-control"' in html
    assert 'class="form-select"' in html
    assert 'class="btn btn-primary"' in html

    assert "form-control-sm" not in html
    assert "form-select-sm" not in html
    assert "btn-sm" not in html


def test_pantalla_mayor_general_estado_usa_ns_select():
    """Valida que el filtro Estado use NeriSoft Select."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_mayor_general(db)

        response = client.get("/contabilidad/libros/mayor-general/")

    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert re.search(
        r'id="lmg-estado"[\s\S]*?data-ns-select[\s\S]*?name="estado"',
        html,
    ) is not None
    assert 'data-ns-select-placeholder="Seleccionar estado"' in html
