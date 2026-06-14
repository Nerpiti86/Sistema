import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _crear_grupo_cliente(db) -> int:
    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("General", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_pais(db) -> int:
    cursor = db.execute(
        """
        INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Argentina", "AR", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_provincia(db, pais_id: int) -> int:
    cursor = db.execute(
        """
        INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?, ?)
        """,
        (pais_id, "Santa Fe", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cuenta_contable(db, cuenta: str, descripcion: str) -> str:
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
            descripcion,
            "DEBE",
            "PATRIMONIAL",
            1,
            0,
            None,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def test_migracion_crea_tabla_clientes():
    """Valida columnas base del maestro operativo de clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA table_info(clientes)").fetchall()

    column_names = {row["name"] for row in rows}

    assert {
        "id",
        "razon_social",
        "nombre_fantasia",
        "grupo_cliente_id",
        "telefono",
        "email",
        "domicilio",
        "codigo_postal",
        "ciudad",
        "pais_id",
        "provincia_id",
        "condicion_iva_codigo",
        "tipo_documento_fiscal_codigo",
        "numero_documento_fiscal",
        "cuenta_deudores_ventas_codigo",
        "cuenta_anticipo_clientes_codigo",
        "activo",
        "orden",
        "observaciones",
        "creado_en",
        "actualizado_en",
    }.issubset(column_names)


def test_clientes_no_tiene_cuenta_ingreso():
    """Valida que la cuenta de ingreso no pertenezca al maestro clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA table_info(clientes)").fetchall()

    column_names = {row["name"] for row in rows}

    assert "cuenta_ingreso_codigo" not in column_names
    assert "cuenta_ingreso_id" not in column_names


def test_clientes_permita_alta_minima_con_grupo():
    """Valida alta minima sin exigir datos fiscales ni domicilio inicial."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)

        db.execute(
            """
            INSERT INTO clientes (razon_social, grupo_cliente_id, creado_en)
            VALUES (?, ?, ?)
            """,
            ("Cliente General", grupo_id, "2026-01-01 10:00:00"),
        )

        cliente = db.execute(
            """
            SELECT razon_social, grupo_cliente_id, activo, orden
            FROM clientes
            WHERE razon_social = ?
            """,
            ("Cliente General",),
        ).fetchone()

    assert cliente["razon_social"] == "Cliente General"
    assert cliente["grupo_cliente_id"] == grupo_id
    assert cliente["activo"] == 1
    assert cliente["orden"] == 0


def test_clientes_permite_nombre_fantasia_y_observaciones():
    """Valida campos administrativos opcionales no fiscales."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)

        db.execute(
            """
            INSERT INTO clientes (
                razon_social,
                nombre_fantasia,
                grupo_cliente_id,
                observaciones,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Cliente Razon Social",
                "Cliente Comercial",
                grupo_id,
                "Observacion administrativa",
                "2026-01-01 10:00:00",
            ),
        )

        cliente = db.execute(
            """
            SELECT razon_social, nombre_fantasia, observaciones
            FROM clientes
            WHERE razon_social = ?
            """,
            ("Cliente Razon Social",),
        ).fetchone()

    assert cliente["nombre_fantasia"] == "Cliente Comercial"
    assert cliente["observaciones"] == "Observacion administrativa"


def test_clientes_rechaza_razon_social_vacia():
    """Valida que razon_social no admita texto vacio ni espacios."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes (razon_social, grupo_cliente_id, creado_en)
                VALUES (?, ?, ?)
                """,
                ("   ", grupo_id, "2026-01-01 10:00:00"),
            )


def test_clientes_rechaza_grupo_cliente_inexistente():
    """Valida FK obligatoria contra grupos_clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes (razon_social, grupo_cliente_id, creado_en)
                VALUES (?, ?, ?)
                """,
                ("Cliente sin grupo", 999, "2026-01-01 10:00:00"),
            )


def test_clientes_rechaza_documento_fiscal_incompleto():
    """Valida que tipo y numero fiscal se carguen juntos o ambos nulos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes (
                    razon_social,
                    grupo_cliente_id,
                    tipo_documento_fiscal_codigo,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                ("Cliente sin numero", grupo_id, "80", "2026-01-01 10:00:00"),
            )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes (
                    razon_social,
                    grupo_cliente_id,
                    numero_documento_fiscal,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                ("Cliente sin tipo", grupo_id, "30700000001", "2026-01-01 10:00:00"),
            )


def test_clientes_rechaza_documento_fiscal_duplicado():
    """Valida unicidad de identificacion fiscal cuando se informa documento."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        get_db().execute(
            """
            INSERT INTO clientes (
                razon_social,
                grupo_cliente_id,
                tipo_documento_fiscal_codigo,
                numero_documento_fiscal,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Cliente Uno", grupo_id, "80", "30700000001", "2026-01-01 10:00:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes (
                    razon_social,
                    grupo_cliente_id,
                    tipo_documento_fiscal_codigo,
                    numero_documento_fiscal,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Cliente Dos",
                    grupo_id,
                    "80",
                    "30700000001",
                    "2026-01-01 10:00:00",
                ),
            )


def test_clientes_referencia_catalogos_fiscales_existentes():
    """Valida FKs contra condiciones_iva y tipos_documento por codigo fiscal."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        get_db().execute(
            """
            INSERT INTO clientes (
                razon_social,
                grupo_cliente_id,
                condicion_iva_codigo,
                tipo_documento_fiscal_codigo,
                numero_documento_fiscal,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Cliente Fiscal",
                grupo_id,
                "5",
                "80",
                "30700000001",
                "2026-01-01 10:00:00",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes (
                    razon_social,
                    grupo_cliente_id,
                    condicion_iva_codigo,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Cliente Fiscal Invalido",
                    grupo_id,
                    "999",
                    "2026-01-01 10:00:00",
                ),
            )


def test_clientes_referencia_geografia_existente():
    """Valida FKs geografica y regla de provincia con pais informado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        pais_id = _crear_pais(db)
        provincia_id = _crear_provincia(db, pais_id)

        db.execute(
            """
            INSERT INTO clientes (
                razon_social,
                grupo_cliente_id,
                pais_id,
                provincia_id,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Cliente Santa Fe",
                grupo_id,
                pais_id,
                provincia_id,
                "2026-01-01 10:00:00",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO clientes (
                    razon_social,
                    grupo_cliente_id,
                    provincia_id,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Cliente Provincia Sin Pais",
                    grupo_id,
                    provincia_id,
                    "2026-01-01 10:00:00",
                ),
            )


def test_clientes_referencia_cuentas_contables_por_codigo():
    """Valida FKs opcionales contra cuentas_contables.cuenta."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        cuenta_deudores = _crear_cuenta_contable(
            db,
            "1.1.01.01.997",
            "Deudores clientes test",
        )
        cuenta_anticipos = _crear_cuenta_contable(
            db,
            "2.1.01.01.997",
            "Anticipos clientes test",
        )

        db.execute(
            """
            INSERT INTO clientes (
                razon_social,
                grupo_cliente_id,
                cuenta_deudores_ventas_codigo,
                cuenta_anticipo_clientes_codigo,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Cliente Cuentas",
                grupo_id,
                cuenta_deudores,
                cuenta_anticipos,
                "2026-01-01 10:00:00",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO clientes (
                    razon_social,
                    grupo_cliente_id,
                    cuenta_deudores_ventas_codigo,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Cliente Cuenta Invalida",
                    grupo_id,
                    "9.9.99.99.999",
                    "2026-01-01 10:00:00",
                ),
            )


def test_clientes_rechaza_activo_invalido_y_orden_negativo():
    """Valida booleano activo y orden no negativo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes (razon_social, grupo_cliente_id, activo, creado_en)
                VALUES (?, ?, ?, ?)
                """,
                ("Cliente Activo Invalido", grupo_id, 2, "2026-01-01 10:00:00"),
            )

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO clientes (razon_social, grupo_cliente_id, orden, creado_en)
                VALUES (?, ?, ?, ?)
                """,
                ("Cliente Orden Invalido", grupo_id, -1, "2026-01-01 10:00:00"),
            )


def test_clientes_crea_indices_operativos():
    """Valida indices base para listados, filtros y documento fiscal."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        rows = get_db().execute("PRAGMA index_list(clientes)").fetchall()

    index_names = {row["name"] for row in rows}

    assert "ix_clientes_activo_razon_social" in index_names
    assert "ix_clientes_grupo_cliente" in index_names
    assert "ix_clientes_pais_provincia" in index_names
    assert "ix_clientes_condicion_iva" in index_names
    assert "ix_clientes_documento_fiscal" in index_names
    assert "ux_clientes_documento_fiscal" in index_names
