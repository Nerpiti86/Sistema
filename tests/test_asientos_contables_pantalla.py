import re

from app import create_app
from app.config import TestConfig
from app.contabilidad.asientos_contables_service import crear_asiento_contable_borrador
from app.db import apply_migrations, get_db


def _insertar_ejercicio_contable_pantalla_para_asientos(db) -> int:
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


def _insertar_cuenta_contable_pantalla_para_asientos(db, cuenta: str) -> str:
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
            f"Cuenta pantalla {cuenta}",
            "DEBE",
            "PATRIMONIAL",
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )

    return cuenta


def test_pantalla_asientos_contables_responde_ok_sin_datos():
    """
    Valida pantalla minima de listado sin asientos cargados.

    El HTML usa IDs cortos y data-* para trazabilidad tecnica:
    tabla SQL, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/asientos-contables/")

    assert response.status_code == 200
    assert b"Asientos contables" in response.data
    assert b"No hay asientos contables cargados" in response.data
    assert b'id="as-listado"' in response.data
    assert b'id="as-tabla"' in response.data
    assert b'id="as-mensaje-sin-datos"' in response.data
    assert b'data-table="asientos_contables"' in response.data
    assert b'data-query="listar_asientos_contables"' in response.data


def test_pantalla_asientos_contables_muestra_asiento_con_ids_y_formato_argentino():
    """
    Valida fila de asientos_contables con ID corto y fecha argentina.

    La pantalla no muestra fecha ISO cruda ni importes enteros en centavos.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _insertar_ejercicio_contable_pantalla_para_asientos(db)
        cuenta_debe = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "1.1.01.01.999",
        )
        cuenta_haber = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "1.1.01.01.998",
        )

        asiento = crear_asiento_contable_borrador(
            {
                "ejercicio_id": ejercicio_id,
                "fecha": "2026-06-10",
                "descripcion": "Asiento pantalla",
            },
            [
                {
                    "cuenta_contable_codigo": cuenta_debe,
                    "nominal_debe_centavos": 100000,
                    "debe_centavos": 100000,
                },
                {
                    "cuenta_contable_codigo": cuenta_haber,
                    "nominal_haber_centavos": 100000,
                    "haber_centavos": 100000,
                },
            ],
        )

        response = client.get("/contabilidad/asientos-contables/")

    assert response.status_code == 200
    assert b"Asiento pantalla" in response.data
    assert f'id="as-row-{asiento["id"]}"'.encode() in response.data
    assert f'data-row-id="{asiento["id"]}"'.encode() in response.data
    assert b"10/06/2026" in response.data
    assert b"2026-06-10" not in response.data
    assert b"Borrador" in response.data
    assert b"ARS/ARS" in response.data
    assert b"1,000000" in response.data
    assert b"1.000,00" in response.data
    html = response.data.decode("utf-8")
    assert re.search(r">\\s*100000\\s*<", html) is None


def test_pantalla_contabilidad_tiene_acceso_corto_a_asientos_contables():
    """
    Valida acceso desde contabilidad con ID corto.

    La trazabilidad de tabla/accion queda en data-table y data-action.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Asientos contables" in response.data
    assert b"/contabilidad/asientos-contables/" in response.data
    assert b'id="as-acceso"' in response.data
    assert b'data-table="asientos_contables"' in response.data
    assert b'data-action="ver_listado_asientos_contables"' in response.data
