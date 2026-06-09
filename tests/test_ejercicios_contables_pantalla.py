from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _insertar_ejercicio_contable_pantalla_para_test(db):
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
            es_primer_ejercicio
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ),
    )


def test_pantalla_ejercicios_contables_responde_ok_sin_datos():
    """
    Valida pantalla minima de solo lectura sin ejercicios cargados.

    El HTML usa IDs cortos y data-* para trazabilidad tecnica:
    tabla SQL, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/")

    assert response.status_code == 200
    assert b"Ejercicios contables" in response.data
    assert b"No hay ejercicios contables cargados" in response.data
    assert b'id="ec-listado"' in response.data
    assert b'id="ec-tabla"' in response.data
    assert b'id="ec-mensaje-sin-datos"' in response.data
    assert b'data-table="ejercicios_contables"' in response.data
    assert b'data-query="listar_ejercicios_contables"' in response.data


def test_pantalla_ejercicios_contables_muestra_ejercicio_activo_con_ids_cortos():
    """
    Valida fila de ejercicios_contables con ID corto y data-row-codigo.

    No se exige ID en cada celda: cada celda usa data-field.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_test(db)

        response = client.get("/contabilidad/ejercicios-contables/")

    assert response.status_code == 200
    assert b"EJ2026" in response.data
    assert b"Ejercicio 2026" in response.data
    assert b'id="ec-row-ej2026"' in response.data
    assert b'data-row-codigo="EJ2026"' in response.data
    assert b'data-field="fecha_desde"' in response.data
    assert b"01/01/2026" in response.data
    assert b"31/12/2026" in response.data
    assert b"2026-01-01" not in response.data
    assert b"2026-12-31" not in response.data
    assert b'data-field="es_primer_ejercicio"' in response.data
    assert b"Es primer ejercicio" in response.data
    assert b'id="ec-activo-resumen"' in response.data


def test_pantalla_contabilidad_tiene_acceso_corto_a_ejercicios_contables():
    """
    Valida acceso desde contabilidad con ID corto.

    La trazabilidad de tabla/consulta queda en data-table y data-query.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Ejercicios contables" in response.data
    assert b"/contabilidad/ejercicios-contables/" in response.data
    assert b'id="ec-acceso"' in response.data
    assert b'data-table="ejercicios_contables"' in response.data
