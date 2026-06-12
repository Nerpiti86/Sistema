from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.shared.medios_operativos_service import (
    activar_medio_operativo,
    actualizar_medio_operativo_desde_formulario,
    crear_medio_operativo_desde_formulario,
    desactivar_medio_operativo,
    normalizar_codigo_medio_operativo_desde_formulario,
    obtener_contexto_listado_medios_operativos,
    obtener_medio_operativo_activo_por_codigo,
)


def test_medios_operativos_service_no_usa_sql_directo():
    """Valida que el service de medios_operativos no ejecute SQL ni use get_db."""
    contenido = Path("app/shared/medios_operativos_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_obtener_contexto_listado_medios_operativos_vacio():
    """Valida contexto inicial del maestro medios operativos sin datos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        contexto = obtener_contexto_listado_medios_operativos()

    assert contexto["cantidad_medios_operativos"] == 0
    assert contexto["cantidad_medios_operativos_activos"] == 0
    assert {"medios_operativos", "medios_operativos_activos"}.issubset(contexto)


def test_crear_medio_operativo_efectivo_desde_formulario():
    """Valida alta manual de medio operativo efectivo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        medio = crear_medio_operativo_desde_formulario(
            {
                "codigo": "1",
                "nombre": "Caja pesos",
                "tipo": "EFECTIVO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "1.1.01.01.001",
                "activo": "1",
                "orden": "10",
            }
        )

    assert medio["codigo"] == "1"
    assert medio["nombre"] == "Caja pesos"
    assert medio["tipo"] == "EFECTIVO"
    assert medio["moneda_codigo"] == "ARS"
    assert medio["cuenta_contable_codigo"] == "1.1.01.01.001"


def test_crear_medio_operativo_banco_propio_desde_formulario():
    """Valida alta manual de medio operativo banco propio."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba("1.1.01.03.001", "Banco Municipal ARS")
        medio = crear_medio_operativo_desde_formulario(
            {
                "codigo": "10",
                "nombre": "Banco Municipal pesos",
                "tipo": "BANCO_PROPIO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "1.1.01.03.001",
                "banco_codigo": "65",
                "plaza": "Rosario",
                "sucursal": "Centro",
                "numero_cuenta": "123456",
                "cuit": "30-00000000-0",
                "activo": "1",
                "orden": "20",
            }
        )

    assert medio["codigo"] == "10"
    assert medio["tipo"] == "BANCO_PROPIO"
    assert medio["banco_codigo"] == "65"
    assert medio["numero_cuenta"] == "123456"


def test_crear_medio_operativo_banco_propio_requiere_banco():
    """Valida que banco propio exija banco asociado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()

        with pytest.raises(ValueError):
            crear_medio_operativo_desde_formulario(
                {
                    "codigo": "10",
                    "nombre": "Banco sin banco",
                    "tipo": "BANCO_PROPIO",
                    "moneda_codigo": "ARS",
                    "cuenta_contable_codigo": "1.1.01.01.001",
                    "activo": "1",
                    "orden": "20",
                }
            )


def test_crear_medio_operativo_requiere_cuenta_imputable():
    """Valida que la cuenta contable del medio operativo sea imputable."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba(imputable=0)

        with pytest.raises(ValueError):
            crear_medio_operativo_desde_formulario(
                {
                    "codigo": "1",
                    "nombre": "Caja pesos",
                    "tipo": "EFECTIVO",
                    "moneda_codigo": "ARS",
                    "cuenta_contable_codigo": "1.1.01.01.001",
                    "activo": "1",
                    "orden": "10",
                }
            )


def test_actualizar_medio_operativo_desde_formulario():
    """Valida edicion manual de medio operativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        crear_medio_operativo_desde_formulario(
            {
                "codigo": "1",
                "nombre": "Caja pesos",
                "tipo": "EFECTIVO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "1.1.01.01.001",
                "activo": "1",
                "orden": "10",
            }
        )
        medio = actualizar_medio_operativo_desde_formulario(
            "1",
            {
                "nombre": "Caja pesos editada",
                "tipo": "EFECTIVO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "1.1.01.01.001",
                "activo": "1",
                "orden": "15",
            },
        )

    assert medio["codigo"] == "1"
    assert medio["nombre"] == "Caja pesos editada"
    assert medio["orden"] == 15


def test_activar_desactivar_medio_operativo():
    """Valida baja logica por activar/desactivar sin borrado fisico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        crear_medio_operativo_desde_formulario(
            {
                "codigo": "1",
                "nombre": "Caja pesos",
                "tipo": "EFECTIVO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "1.1.01.01.001",
                "activo": "1",
                "orden": "10",
            }
        )
        medio_desactivado = desactivar_medio_operativo("1")
        medio_activado = activar_medio_operativo("1")

    assert medio_desactivado["activo"] == 0
    assert medio_desactivado["esta_activo"] is False
    assert medio_activado["activo"] == 1
    assert medio_activado["esta_activo"] is True


def test_obtener_medio_operativo_activo_por_codigo():
    """Valida obtencion funcional por codigo visual operativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        crear_medio_operativo_desde_formulario(
            {
                "codigo": "1",
                "nombre": "Caja pesos",
                "tipo": "EFECTIVO",
                "moneda_codigo": "ARS",
                "cuenta_contable_codigo": "1.1.01.01.001",
                "activo": "1",
                "orden": "10",
            }
        )
        medio = obtener_medio_operativo_activo_por_codigo(" 1 ")

    assert medio["codigo"] == "1"
    assert medio["descripcion_select"] == "1 - Caja pesos"


def test_normalizar_codigo_medio_operativo_desde_formulario():
    """Valida normalizacion de codigo visual de medio operativo."""
    assert normalizar_codigo_medio_operativo_desde_formulario(" caja1 ") == "CAJA1"


def test_normalizar_codigo_medio_operativo_desde_formulario_rechaza_vacio():
    """Valida rechazo de codigo vacio desde formulario."""
    with pytest.raises(ValueError):
        normalizar_codigo_medio_operativo_desde_formulario("")


def _insertar_cuenta_prueba(
    cuenta="1.1.01.01.001",
    descripcion="Caja ARS",
    imputable=1,
):
    get_db().execute(
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
            imputable,
            1,
            "2026-01-01 10:00:00",
        ),
    )
