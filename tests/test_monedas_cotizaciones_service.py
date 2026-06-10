from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.shared.monedas_cotizaciones_repository import crear_moneda_cotizacion
from app.shared.monedas_cotizaciones_service import (
    crear_moneda_cotizacion_desde_formulario,
    obtener_contexto_cotizaciones_por_par,
    obtener_contexto_cotizaciones_recientes,
    obtener_ultima_cotizacion_para_operacion,
)


def test_monedas_cotizaciones_service_no_usa_sql_directo():
    """Valida que el service de cotizaciones no ejecute SQL ni use get_db."""
    contenido = Path("app/shared/monedas_cotizaciones_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_crear_moneda_cotizacion_desde_formulario():
    """Valida alta de cotizacion desde datos tipo formulario."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cotizacion = crear_moneda_cotizacion_desde_formulario(
            {
                "moneda_origen_codigo": " usd ",
                "moneda_destino_codigo": " ars ",
                "fecha": "10/06/2026",
                "tipo": " cierre ",
                "cotizacion": "1.250,500000",
                "fuente": "Manual",
                "observaciones": "Carga inicial",
            }
        )

    assert cotizacion["moneda_origen_codigo"] == "USD"
    assert cotizacion["moneda_destino_codigo"] == "ARS"
    assert cotizacion["fecha"] == "2026-06-10"
    assert cotizacion["fecha_argentina"] == "10/06/2026"
    assert cotizacion["cotizacion_1000000"] == 1250500000
    assert cotizacion["cotizacion_argentina"] == "1.250,500000"


def test_obtener_contexto_cotizaciones_recientes():
    """Valida contexto chico de cotizaciones recientes."""
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

        contexto = obtener_contexto_cotizaciones_recientes(10)

    assert contexto["cantidad_cotizaciones"] == 1
    assert contexto["cotizaciones"][0]["par_codigo"] == "USD/ARS"
    assert contexto["cotizaciones"][0]["fecha_argentina"] == "10/06/2026"


def test_obtener_contexto_cotizaciones_por_par():
    """Valida contexto filtrado por par de monedas."""
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

        contexto = obtener_contexto_cotizaciones_por_par(
            "USD",
            "ARS",
            "CIERRE",
            10,
        )

    assert contexto["cantidad_cotizaciones"] == 1
    assert contexto["cotizaciones"][0]["cotizacion_argentina"] == "1.250,500000"


def test_obtener_ultima_cotizacion_para_operacion_con_fecha_argentina():
    """Valida ultima cotizacion usando fecha limite desde formulario."""
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

        cotizacion = obtener_ultima_cotizacion_para_operacion(
            "USD",
            "ARS",
            "CIERRE",
            "09/06/2026",
        )

    assert cotizacion["fecha"] == "2026-06-09"
    assert cotizacion["cotizacion_argentina"] == "1.240,000000"


def test_obtener_ultima_cotizacion_para_operacion_rechaza_inexistente():
    """Valida error si no existe cotizacion para el par."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            obtener_ultima_cotizacion_para_operacion(
                "USD",
                "ARS",
                "CIERRE",
                "10/06/2026",
            )


def test_crear_moneda_cotizacion_desde_formulario_rechaza_decimal_invalido():
    """Valida escala fija de seis decimales para cotizacion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            crear_moneda_cotizacion_desde_formulario(
                {
                    "moneda_origen_codigo": "USD",
                    "moneda_destino_codigo": "ARS",
                    "fecha": "10/06/2026",
                    "tipo": "CIERRE",
                    "cotizacion": "1250,50",
                }
            )
