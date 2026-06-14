import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _crear_cuenta_contable_ingreso(db, cuenta: str = "4.1.01.01.997") -> str:
    """Crea una cuenta imputable de prueba para validar FK de ingreso sugerido."""
    db.execute(
        """
        INSERT INTO cuentas_contables (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            sumarizadora,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cuenta,
            "Ingresos por servicios test",
            "HABER",
            "RESULTADO",
            1,
            0,
            None,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def test_migracion_crea_tabla_articulos_venta():
    """Valida columnas base del maestro de productos o servicios vendibles."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA table_info(articulos_venta)").fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "nombre",
        "tipo",
        "moneda_codigo",
        "precio_unitario_sugerido_centavos",
        "cuenta_ingreso_codigo",
        "activo",
        "orden",
        "observaciones",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)
    columna_precio_escala_cotizacion = "precio_unitario_sugerido_" + "1000000"
    assert columna_precio_escala_cotizacion not in column_names


def test_articulos_venta_permite_alta_minima_servicio():
    """Valida alta minima de un servicio vendible con precio sugerido default."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
            """
            INSERT INTO articulos_venta (
                nombre,
                tipo,
                moneda_codigo,
                creado_en
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "Consulta profesional",
                "SERVICIO",
                "ARS",
                "2026-01-01 10:00:00",
            ),
        )

        articulo = db.execute(
            """
            SELECT nombre,
                   tipo,
                   moneda_codigo,
                   precio_unitario_sugerido_centavos,
                   activo,
                   orden
            FROM articulos_venta
            WHERE nombre = ?
            """,
            ("Consulta profesional",),
        ).fetchone()

    assert articulo["nombre"] == "Consulta profesional"
    assert articulo["tipo"] == "SERVICIO"
    assert articulo["moneda_codigo"] == "ARS"
    assert articulo["precio_unitario_sugerido_centavos"] == 0
    assert articulo["activo"] == 1
    assert articulo["orden"] == 0


def test_articulos_venta_permite_producto_con_precio_sugerido():
    """Valida producto vendible con precio sugerido general no obligatorio."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
            """
            INSERT INTO articulos_venta (
                nombre,
                tipo,
                moneda_codigo,
                precio_unitario_sugerido_centavos,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Producto odontologico test",
                "PRODUCTO",
                "ARS",
                1250000,
                "2026-01-01 10:00:00",
            ),
        )

        articulo = db.execute(
            """
            SELECT precio_unitario_sugerido_centavos
            FROM articulos_venta
            WHERE nombre = ?
            """,
            ("Producto odontologico test",),
        ).fetchone()

    assert articulo["precio_unitario_sugerido_centavos"] == 1250000


def test_articulos_venta_rechaza_nombre_vacio():
    """Valida que el producto o servicio tenga nombre visible no vacio."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "   ",
                    "SERVICIO",
                    "ARS",
                    "2026-01-01 10:00:00",
                ),
            )


def test_articulos_venta_rechaza_nombre_duplicado():
    """Valida unicidad simple del nombre visible del producto o servicio."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        db.execute(
            """
            INSERT INTO articulos_venta (
                nombre,
                tipo,
                moneda_codigo,
                creado_en
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "Sesion de psicologia",
                "SERVICIO",
                "ARS",
                "2026-01-01 10:00:00",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "sesion de psicologia",
                    "SERVICIO",
                    "ARS",
                    "2026-01-01 10:01:00",
                ),
            )


def test_articulos_venta_rechaza_tipo_invalido():
    """Valida tipos cerrados PRODUCTO o SERVICIO."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Concepto invalido",
                    "OTRO",
                    "ARS",
                    "2026-01-01 10:00:00",
                ),
            )


def test_articulos_venta_referencia_moneda_existente():
    """Valida FK contra el maestro transversal de monedas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Servicio moneda invalida",
                    "SERVICIO",
                    "GBP",
                    "2026-01-01 10:00:00",
                ),
            )


def test_articulos_venta_rechaza_precio_sugerido_negativo():
    """Valida que el precio sugerido general no sea negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    precio_unitario_sugerido_centavos,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Servicio precio invalido",
                    "SERVICIO",
                    "ARS",
                    -1,
                    "2026-01-01 10:00:00",
                ),
            )


def test_articulos_venta_referencia_cuenta_ingreso_existente():
    """Valida FK opcional contra cuentas_contables.cuenta para ingreso sugerido."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cuenta_ingreso = _crear_cuenta_contable_ingreso(db)

        db.execute(
            """
            INSERT INTO articulos_venta (
                nombre,
                tipo,
                moneda_codigo,
                cuenta_ingreso_codigo,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Servicio con cuenta ingreso",
                "SERVICIO",
                "ARS",
                cuenta_ingreso,
                "2026-01-01 10:00:00",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    cuenta_ingreso_codigo,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Servicio cuenta invalida",
                    "SERVICIO",
                    "ARS",
                    "9.9.99.99.999",
                    "2026-01-01 10:00:00",
                ),
            )


def test_articulos_venta_rechaza_activo_invalido_y_orden_negativo():
    """Valida booleano activo y orden no negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    activo,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Servicio activo invalido",
                    "SERVICIO",
                    "ARS",
                    2,
                    "2026-01-01 10:00:00",
                ),
            )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO articulos_venta (
                    nombre,
                    tipo,
                    moneda_codigo,
                    orden,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Servicio orden invalido",
                    "SERVICIO",
                    "ARS",
                    -1,
                    "2026-01-01 10:00:00",
                ),
            )


def test_articulos_venta_crea_indices_operativos():
    """Valida indices base para listados, selectores y filtros operativos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA index_list(articulos_venta)").fetchall()

    index_names = {row["name"] for row in rows}

    assert "ux_articulos_venta_nombre" in index_names
    assert "ix_articulos_venta_activo_nombre" in index_names
    assert "ix_articulos_venta_tipo" in index_names
    assert "ix_articulos_venta_moneda" in index_names
    assert "ix_articulos_venta_cuenta_ingreso" in index_names
