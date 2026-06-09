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
            bloqueado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        ),
    )


def test_pantalla_ejercicios_contables_responde_ok_sin_datos():
    """
    Valida pantalla minima de solo lectura sin ejercicios cargados.

    En TestConfig se usa SQLite :memory:. El request se ejecuta dentro
    del mismo app_context para conservar la misma conexion de test.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/ejercicios-contables/")

    assert response.status_code == 200
    assert b"Ejercicios contables" in response.data
    assert b"No hay ejercicios contables cargados" in response.data
    assert (
        b'id="ejercicios_contables__listar_ejercicios_contables__tabla"'
        in response.data
    )
    assert (
        b'id="ejercicios_contables__listar_ejercicios_contables__mensaje_sin_datos"'
        in response.data
    )


def test_pantalla_ejercicios_contables_muestra_ejercicio_activo_con_ids_sql():
    """
    Valida IDs HTML relacionados a tabla y consulta del listado.

    El request queda dentro del mismo app_context para conservar la base
    SQLite :memory: usada por los tests.
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
    assert (
        b'id="ejercicios_contables__listar_ejercicios_contables__fila__ej2026"'
        in response.data
    )
    assert (
        b'id="ejercicios_contables__listar_ejercicios_contables__campo_codigo__ej2026"'
        in response.data
    )
    assert (
        b'id="ejercicios_contables__obtener_contexto_listado_ejercicios_contables__activo"'
        in response.data
    )


def test_pantalla_contabilidad_tiene_acceso_identificable_a_ejercicios_contables():
    """Valida acceso identificable desde contabilidad al listado de ejercicios."""
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Ejercicios contables" in response.data
    assert b"/contabilidad/ejercicios-contables/" in response.data
    assert (
        b'id="ejercicios_contables__obtener_contexto_listado_ejercicios_contables__acceso"'
        in response.data
    )
