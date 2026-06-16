import re
from urllib.parse import urlencode

from app import create_app
from app.config import TestConfig
from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_automatico_confirmado,
)
from app.db import apply_migrations, get_db


CUENTA_MAYOR = "1.1.03.01.993"
CUENTA_CONTRA = "4.1.01.01.993"


def _insertar_ejercicio_mayor_cuenta(db) -> int:
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
            "Ejercicio Mayor Cuenta",
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


def _insertar_cuenta_mayor(
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


def _crear_asiento_mayor(
    ejercicio_id: int,
    *,
    fecha: str,
    descripcion: str,
    debe_mayor_centavos: int,
    haber_mayor_centavos: int,
) -> dict:
    if debe_mayor_centavos > 0:
        detalle_mayor = {
            "cuenta_contable_codigo": CUENTA_MAYOR,
            "descripcion": "Linea mayor debe",
            "nominal_debe_centavos": debe_mayor_centavos,
            "debe_centavos": debe_mayor_centavos,
        }
        detalle_contra = {
            "cuenta_contable_codigo": CUENTA_CONTRA,
            "descripcion": "Linea contra haber",
            "nominal_haber_centavos": debe_mayor_centavos,
            "haber_centavos": debe_mayor_centavos,
        }
    else:
        detalle_mayor = {
            "cuenta_contable_codigo": CUENTA_MAYOR,
            "descripcion": "Linea mayor haber",
            "nominal_haber_centavos": haber_mayor_centavos,
            "haber_centavos": haber_mayor_centavos,
        }
        detalle_contra = {
            "cuenta_contable_codigo": CUENTA_CONTRA,
            "descripcion": "Linea contra debe",
            "nominal_debe_centavos": haber_mayor_centavos,
            "debe_centavos": haber_mayor_centavos,
        }

    return crear_asiento_contable_automatico_confirmado(
        {
            "ejercicio_id": ejercicio_id,
            "fecha": fecha,
            "descripcion": descripcion,
            "tipo": "VENTA",
        },
        [
            detalle_mayor,
            detalle_contra,
        ],
    )


def _crear_datos_mayor_cuenta(db) -> int:
    ejercicio_id = _insertar_ejercicio_mayor_cuenta(db)
    _insertar_cuenta_mayor(
        db,
        CUENTA_MAYOR,
        "Deudores por ventas pantalla mayor",
        "DEBE",
    )
    _insertar_cuenta_mayor(
        db,
        CUENTA_CONTRA,
        "Ingresos por servicios pantalla mayor",
        "HABER",
    )

    _crear_asiento_mayor(
        ejercicio_id,
        fecha="2026-05-31",
        descripcion="Comprobante: SI | Sujeto: Inicial",
        debe_mayor_centavos=1000000,
        haber_mayor_centavos=0,
    )
    _crear_asiento_mayor(
        ejercicio_id,
        fecha="2026-06-10",
        descripcion="Comprobante: FC C 0001-00000001 | Sujeto: Cliente mayor",
        debe_mayor_centavos=3500000,
        haber_mayor_centavos=0,
    )
    _crear_asiento_mayor(
        ejercicio_id,
        fecha="2026-06-20",
        descripcion="Comprobante: NC C 0001-00000001 | Sujeto: Cliente mayor",
        debe_mayor_centavos=0,
        haber_mayor_centavos=500000,
    )

    return ejercicio_id


def test_pantalla_mayor_por_cuenta_responde_ok_sin_cuenta_seleccionada():
    """Valida pantalla inicial con selector de cuenta y sin reporte."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_mayor_cuenta(db)
        _insertar_cuenta_mayor(
            db,
            CUENTA_MAYOR,
            "Deudores por ventas pantalla mayor",
            "DEBE",
        )

        response = client.get("/contabilidad/libros/mayor-cuenta/")

    assert response.status_code == 200
    assert b"Libro mayor por cuenta" in response.data
    assert b"Seleccione una cuenta contable" in response.data
    assert b'id="lmc-listado"' in response.data
    assert b'id="lmc-filtros"' in response.data
    assert b'id="lmc-resumen"' in response.data
    assert b'id="lmc-tabla"' in response.data
    assert CUENTA_MAYOR.encode() in response.data
    assert b'data-query="obtener_contexto_pantalla_mayor_por_cuenta"' in response.data


def test_pantalla_mayor_por_cuenta_muestra_saldos_y_movimientos():
    """Valida mayor de cuenta con saldo inicial, movimientos y saldo final."""
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _crear_datos_mayor_cuenta(db)

        query = urlencode(
            {
                "cuenta_contable_codigo": CUENTA_MAYOR,
                "fecha_desde": "2026-06-01",
                "fecha_hasta": "2026-06-30",
            }
        )
        response = client.get(f"/contabilidad/libros/mayor-cuenta/?{query}")

    assert response.status_code == 200
    assert b"Libro mayor por cuenta" in response.data
    assert b"Deudores por ventas pantalla mayor" in response.data
    assert b"Saldo habitual DEBE" in response.data
    assert b"10.000,00" in response.data
    assert b"35.000,00" in response.data
    assert b"5.000,00" in response.data
    assert b"30.000,00" in response.data
    assert b"40.000,00" in response.data
    assert b"45.000,00" in response.data
    assert b"FC C 0001-00000001" in response.data
    assert b"NC C 0001-00000001" in response.data
    assert b"Cliente mayor" in response.data
    assert b"EJ2026-0000002" in response.data
    assert b"EJ2026-0000003" in response.data
    assert b'id="lmc-saldo-inicial"' in response.data
    assert b'id="lmc-saldo-final"' in response.data

    html = response.data.decode("utf-8")
    assert re.search(r">\\s*3500000\\s*<", html) is None
    assert re.search(r">\\s*4000000\\s*<", html) is None


def test_pantalla_contabilidad_tiene_acceso_a_mayor_por_cuenta():
    """Valida acceso desde el índice de Contabilidad."""
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Libro mayor por cuenta" in response.data
    assert b"/contabilidad/libros/mayor-cuenta/" in response.data
    assert b'id="lmc-acceso"' in response.data
    assert b'data-table="asientos_contables_detalle"' in response.data
    assert b'data-action="ver_mayor_por_cuenta"' in response.data
