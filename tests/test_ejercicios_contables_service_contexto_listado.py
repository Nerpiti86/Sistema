from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.ejercicios_contables_service import (
    obtener_contexto_listado_ejercicios_contables,
)


def test_obtener_contexto_listado_ejercicios_contables_devuelve_contexto_chico():
    """Valida contexto de pantalla sin cargar datos operativos vinculados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

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

        contexto_listado = obtener_contexto_listado_ejercicios_contables()

    assert contexto_listado["cantidad_ejercicios_contables"] == 1
    assert contexto_listado["ejercicio_contable_activo"]["codigo"] == "EJ2026"
    assert (
        contexto_listado["ejercicio_contable_activo"]["fecha_desde_argentina"]
        == "01/01/2026"
    )
    assert (
        contexto_listado["ejercicio_contable_activo"]["fecha_hasta_argentina"]
        == "31/12/2026"
    )
    assert contexto_listado["ejercicios_contables"][0]["codigo"] == "EJ2026"
    assert (
        contexto_listado["ejercicios_contables"][0]["fecha_desde"]
        == "2026-01-01"
    )
    assert (
        contexto_listado["ejercicios_contables"][0]["fecha_desde_argentina"]
        == "01/01/2026"
    )
