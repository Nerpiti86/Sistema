import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.monedas_cotizaciones_repository import (
    crear_moneda_cotizacion,
    listar_monedas_cotizaciones_por_par,
    listar_monedas_cotizaciones_recientes,
    obtener_moneda_cotizacion,
    obtener_ultima_moneda_cotizacion,
)


def test_crear_moneda_cotizacion_devuelve_fila_normalizada():
    """Valida alta repository de cotizacion transversal."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cotizacion = crear_moneda_cotizacion(
            {
                "moneda_origen_codigo": "usd",
                "moneda_destino_codigo": "ars",
                "fecha": "2026-06-10",
                "tipo": "cierre",
                "cotizacion_1000000": 1250500000,
                "fuente": "Manual",
                "observaciones": "Carga inicial",
            }
        )

    assert cotizacion["moneda_origen_codigo"] == "USD"
    assert cotizacion["moneda_destino_codigo"] == "ARS"
    assert cotizacion["tipo"] == "CIERRE"
    assert cotizacion["cotizacion_1000000"] == 1250500000
    assert cotizacion["par_codigo"] == "USD/ARS"


def test_crear_moneda_cotizacion_rechaza_duplicada():
    """Valida unicidad por par, fecha y tipo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        datos = {
            "moneda_origen_codigo": "USD",
            "moneda_destino_codigo": "ARS",
            "fecha": "2026-06-10",
            "tipo": "CIERRE",
            "cotizacion_1000000": 1250500000,
        }

        crear_moneda_cotizacion(datos)

        with pytest.raises(ValueError):
            crear_moneda_cotizacion(datos)


def test_crear_moneda_cotizacion_rechaza_misma_moneda():
    """Valida que el par no relacione una moneda consigo misma."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_moneda_cotizacion(
                {
                    "moneda_origen_codigo": "ARS",
                    "moneda_destino_codigo": "ARS",
                    "fecha": "2026-06-10",
                    "tipo": "CIERRE",
                    "cotizacion_1000000": 1000000,
                }
            )


def test_crear_moneda_cotizacion_rechaza_moneda_inactiva():
    """Valida que no se carguen cotizaciones nuevas para monedas inactivas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute(
            "UPDATE monedas SET activa = 0 WHERE codigo = ?",
            ("EUR",),
        )

        with pytest.raises(ValueError):
            crear_moneda_cotizacion(
                {
                    "moneda_origen_codigo": "EUR",
                    "moneda_destino_codigo": "ARS",
                    "fecha": "2026-06-10",
                    "tipo": "CIERRE",
                    "cotizacion_1000000": 1350000000,
                }
            )


def test_obtener_moneda_cotizacion_devuelve_puntual():
    """Valida busqueda puntual por par, fecha y tipo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_moneda_cotizacion(
            {
                "moneda_origen_codigo": "USD",
                "moneda_destino_codigo": "ARS",
                "fecha": "2026-06-10",
                "tipo": "CIERRE",
                "cotizacion_1000000": 1250500000,
            }
        )

        cotizacion = obtener_moneda_cotizacion(
            "usd",
            "ars",
            "2026-06-10",
            "cierre",
        )

    assert cotizacion is not None
    assert cotizacion["par_codigo"] == "USD/ARS"


def test_obtener_moneda_cotizacion_inexistente_devuelve_none():
    """Valida respuesta nula para cotizacion inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cotizacion = obtener_moneda_cotizacion(
            "USD",
            "ARS",
            "2026-06-10",
            "CIERRE",
        )

    assert cotizacion is None


def test_obtener_ultima_moneda_cotizacion_respeta_fecha_hasta():
    """Valida ultima cotizacion disponible hasta una fecha."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_moneda_cotizacion(
            {
                "moneda_origen_codigo": "USD",
                "moneda_destino_codigo": "ARS",
                "fecha": "2026-06-09",
                "tipo": "CIERRE",
                "cotizacion_1000000": 1240000000,
            }
        )
        crear_moneda_cotizacion(
            {
                "moneda_origen_codigo": "USD",
                "moneda_destino_codigo": "ARS",
                "fecha": "2026-06-10",
                "tipo": "CIERRE",
                "cotizacion_1000000": 1250500000,
            }
        )

        cotizacion = obtener_ultima_moneda_cotizacion(
            "USD",
            "ARS",
            "CIERRE",
            "2026-06-09",
        )

    assert cotizacion is not None
    assert cotizacion["fecha"] == "2026-06-09"
    assert cotizacion["cotizacion_1000000"] == 1240000000


def test_listar_monedas_cotizaciones_por_par_ordena_descendente():
    """Valida listado limitado de cotizaciones por par."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_moneda_cotizacion(
            {
                "moneda_origen_codigo": "USD",
                "moneda_destino_codigo": "ARS",
                "fecha": "2026-06-09",
                "tipo": "CIERRE",
                "cotizacion_1000000": 1240000000,
            }
        )
        crear_moneda_cotizacion(
            {
                "moneda_origen_codigo": "USD",
                "moneda_destino_codigo": "ARS",
                "fecha": "2026-06-10",
                "tipo": "CIERRE",
                "cotizacion_1000000": 1250500000,
            }
        )

        cotizaciones = listar_monedas_cotizaciones_por_par(
            "USD",
            "ARS",
            "CIERRE",
            10,
        )

    assert [cotizacion["fecha"] for cotizacion in cotizaciones] == [
        "2026-06-10",
        "2026-06-09",
    ]


def test_listar_monedas_cotizaciones_recientes_respeta_limite():
    """Valida limite explicito en listado reciente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_moneda_cotizacion(
            {
                "moneda_origen_codigo": "USD",
                "moneda_destino_codigo": "ARS",
                "fecha": "2026-06-09",
                "tipo": "CIERRE",
                "cotizacion_1000000": 1240000000,
            }
        )
        crear_moneda_cotizacion(
            {
                "moneda_origen_codigo": "EUR",
                "moneda_destino_codigo": "ARS",
                "fecha": "2026-06-10",
                "tipo": "CIERRE",
                "cotizacion_1000000": 1350000000,
            }
        )

        cotizaciones = listar_monedas_cotizaciones_recientes(1)

    assert len(cotizaciones) == 1
    assert cotizaciones[0]["fecha"] == "2026-06-10"


def test_repository_rechaza_fecha_invalida():
    """Valida fecha real ISO en repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_moneda_cotizacion(
                {
                    "moneda_origen_codigo": "USD",
                    "moneda_destino_codigo": "ARS",
                    "fecha": "2026-02-31",
                    "tipo": "CIERRE",
                    "cotizacion_1000000": 1250500000,
                }
            )


def test_repository_rechaza_limite_invalido():
    """Valida limite maximo de consultas para cotizaciones."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            listar_monedas_cotizaciones_recientes(0)
