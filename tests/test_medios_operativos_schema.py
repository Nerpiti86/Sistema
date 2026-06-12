import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_migracion_crea_tabla_medios_operativos():
    """Valida columnas base del maestro transversal medios_operativos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA table_info(medios_operativos)").fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "codigo",
        "nombre",
        "tipo",
        "requiere_cotizacion",
        "cotizacion_default_centavos",
        "banco_codigo",
        "plaza",
        "sucursal",
        "numero_cuenta",
        "cuenta_contable_codigo",
        "moneda_codigo",
        "cuit",
        "activo",
        "orden",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_medios_operativos_rechaza_codigo_duplicado():
    """Valida que codigo visual del medio operativo sea unico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()
        _insertar_medio_prueba("1")

        with pytest.raises(sqlite3.IntegrityError):
            _insertar_medio_prueba("1")


def test_medios_operativos_rechaza_tipo_invalido():
    """Valida tipos cerrados de medios operativos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()

        with pytest.raises(sqlite3.IntegrityError):
            _insertar_medio_prueba("1", tipo="OTRO")


def test_medios_operativos_rechaza_activo_invalido():
    """Valida que activo sea booleano entero 0/1."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba()

        with pytest.raises(sqlite3.IntegrityError):
            _insertar_medio_prueba("1", activo=2)


def _insertar_cuenta_prueba():
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
            "1.1.01.01.001",
            "Caja ARS",
            "DEBE",
            "PATRIMONIAL",
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )


def _insertar_medio_prueba(codigo, tipo="EFECTIVO", activo=1):
    get_db().execute(
        """
        INSERT INTO medios_operativos (
            codigo,
            nombre,
            tipo,
            requiere_cotizacion,
            cotizacion_default_centavos,
            cuenta_contable_codigo,
            moneda_codigo,
            activo,
            orden,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            codigo,
            "Caja pesos",
            tipo,
            0,
            None,
            "1.1.01.01.001",
            "ARS",
            activo,
            10,
            "2026-01-01 10:00:00",
        ),
    )
