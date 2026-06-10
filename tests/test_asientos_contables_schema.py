import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _crear_app():
    """Crea app de test; cada test carga migraciones dentro del mismo contexto."""
    return create_app(TestConfig)


def _primer_ejercicio_id(db) -> int:
    fila = db.execute(
        """
        SELECT id
        FROM ejercicios_contables
        ORDER BY id
        LIMIT 1
        """
    ).fetchone()

    if fila is not None:
        return int(fila["id"])

    db.execute(
        """
        INSERT INTO ejercicios_contables (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            creado_en,
            fase_cierre,
            bloqueado,
            es_primer_ejercicio
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "2026",
            "Ejercicio test asientos",
            "2026-01-01",
            "2026-12-31",
            "ABIERTO",
            1,
            "2026-01-01 00:00:00",
            "ABIERTO",
            0,
            1,
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def _cuenta_imputable(db) -> str:
    fila = db.execute(
        """
        SELECT cuenta
        FROM cuentas_contables
        WHERE imputable = 1
        ORDER BY cuenta
        LIMIT 1
        """
    ).fetchone()

    if fila is not None:
        return str(fila["cuenta"])

    cuenta = "1.1.01.01.999"

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
            "Cuenta test asientos",
            "DEBE",
            "PATRIMONIAL",
            1,
            1,
            "2026-01-01 00:00:00",
        ),
    )

    return cuenta


def _crear_asiento_base(
    db,
    ejercicio_id: int,
    *,
    moneda_origen_codigo: str = "ARS",
    moneda_destino_codigo: str = "ARS",
    cotizacion_id: int | None = None,
    cotizacion_1000000: int = 1000000,
) -> int:
    db.execute(
        """
        INSERT INTO asientos_contables (
            ejercicio_id,
            fecha,
            descripcion,
            moneda_origen_codigo,
            moneda_destino_codigo,
            cotizacion_id,
            cotizacion_fecha,
            cotizacion_tipo,
            cotizacion_1000000,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ejercicio_id,
            "2026-06-10",
            "Asiento de prueba",
            moneda_origen_codigo,
            moneda_destino_codigo,
            cotizacion_id,
            "2026-06-10",
            "CIERRE",
            cotizacion_1000000,
            "2026-06-10 10:00:00",
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def _crear_cotizacion_usd_ars(db) -> int:
    db.execute(
        """
        INSERT INTO monedas_cotizaciones (
            moneda_origen_codigo,
            moneda_destino_codigo,
            fecha,
            tipo,
            cotizacion_1000000,
            fuente,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "USD",
            "ARS",
            "2026-06-10",
            "CIERRE",
            1250500000,
            "Manual",
            "2026-06-10 10:00:00",
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def test_migracion_crea_tablas_asientos_contables():
    """
    Valida que la migracion arme cabecera y detalle.

    La estructura base debe quedar disponible para asientos puros y futuros
    asientos generados desde gestion.
    """
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        tablas = {
            fila["name"]
            for fila in db.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

    assert "asientos_contables" in tablas
    assert "asientos_contables_detalle" in tablas


def test_asientos_contables_tiene_columnas_monetarias():
    """
    Valida snapshot monetario en cabecera de asiento.

    El asiento confirmado debe conservar moneda, tipo, fecha y cotizacion usada,
    aunque luego cambie la tabla transversal de cotizaciones.
    """
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        columnas = {
            fila["name"]
            for fila in get_db().execute(
                "PRAGMA table_info(asientos_contables)"
            ).fetchall()
        }

    assert {
        "moneda_origen_codigo",
        "moneda_destino_codigo",
        "cotizacion_id",
        "cotizacion_fecha",
        "cotizacion_tipo",
        "cotizacion_1000000",
    }.issubset(columnas)


def test_asientos_contables_detalle_tiene_nominal_y_ars_contable():
    """
    Valida nominal por renglon y ARS contable.

    Toda la contabilidad se expresa en ARS mediante debe_centavos/haber_centavos,
    pero cada renglon conserva moneda real, cotizacion y nominal.
    """
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        columnas = {
            fila["name"]
            for fila in get_db().execute(
                "PRAGMA table_info(asientos_contables_detalle)"
            ).fetchall()
        }

    assert {
        "moneda_codigo",
        "cotizacion_id",
        "cotizacion_fecha",
        "cotizacion_tipo",
        "cotizacion_1000000",
        "nominal_debe_centavos",
        "nominal_haber_centavos",
        "debe_centavos",
        "haber_centavos",
    }.issubset(columnas)

    assert "_".join(["debe", "moneda", "centavos"]) not in columnas
    assert "_".join(["haber", "moneda", "centavos"]) not in columnas


def test_asiento_permite_ars_ars_con_cotizacion_uno():
    """Valida asiento en moneda local sin conversion."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)

        asiento_id = _crear_asiento_base(
            db,
            ejercicio_id,
            moneda_origen_codigo="ARS",
            moneda_destino_codigo="ARS",
            cotizacion_1000000=1000000,
        )

        fila = db.execute(
            """
            SELECT moneda_origen_codigo,
                   moneda_destino_codigo,
                   cotizacion_1000000
            FROM asientos_contables
            WHERE id = ?
            """,
            (asiento_id,),
        ).fetchone()

    assert fila["moneda_origen_codigo"] == "ARS"
    assert fila["moneda_destino_codigo"] == "ARS"
    assert fila["cotizacion_1000000"] == 1000000


def test_asiento_rechaza_ars_ars_con_cotizacion_distinta_de_uno():
    """Valida que misma moneda no admita cotizacion distinta de 1."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)

        with pytest.raises(sqlite3.IntegrityError):
            _crear_asiento_base(
                db,
                ejercicio_id,
                moneda_origen_codigo="ARS",
                moneda_destino_codigo="ARS",
                cotizacion_1000000=1250000000,
            )


def test_asiento_permite_usd_ars_con_snapshot_de_cotizacion():
    """Valida asiento en moneda extranjera con snapshot de cotizacion."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)
        cotizacion_id = _crear_cotizacion_usd_ars(db)

        asiento_id = _crear_asiento_base(
            db,
            ejercicio_id,
            moneda_origen_codigo="USD",
            moneda_destino_codigo="ARS",
            cotizacion_id=cotizacion_id,
            cotizacion_1000000=1250500000,
        )

        fila = db.execute(
            """
            SELECT moneda_origen_codigo,
                   moneda_destino_codigo,
                   cotizacion_id,
                   cotizacion_1000000
            FROM asientos_contables
            WHERE id = ?
            """,
            (asiento_id,),
        ).fetchone()

    assert fila["moneda_origen_codigo"] == "USD"
    assert fila["moneda_destino_codigo"] == "ARS"
    assert fila["cotizacion_id"] == cotizacion_id
    assert fila["cotizacion_1000000"] == 1250500000


def test_asiento_rechaza_cotizacion_no_positiva():
    """Valida que la cotizacion snapshot sea positiva."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)

        with pytest.raises(sqlite3.IntegrityError):
            _crear_asiento_base(
                db,
                ejercicio_id,
                moneda_origen_codigo="USD",
                moneda_destino_codigo="ARS",
                cotizacion_1000000=0,
            )


def test_asiento_rechaza_moneda_inexistente():
    """Valida integridad contra maestro transversal de monedas."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)

        with pytest.raises(sqlite3.IntegrityError):
            _crear_asiento_base(
                db,
                ejercicio_id,
                moneda_origen_codigo="GBP",
                moneda_destino_codigo="ARS",
                cotizacion_1000000=1500000000,
            )


def test_detalle_rechaza_debe_y_haber_contable_simultaneos():
    """Valida que una linea no pueda imputar debe y haber a la vez."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)
        asiento_id = _crear_asiento_base(db, ejercicio_id)
        cuenta = _cuenta_imputable(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO asientos_contables_detalle (
                    asiento_id,
                    renglon,
                    cuenta_contable_codigo,
                    moneda_codigo,
                    cotizacion_fecha,
                    nominal_debe_centavos,
                    debe_centavos,
                    haber_centavos
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asiento_id,
                    1,
                    cuenta,
                    "ARS",
                    "2026-06-10",
                    10000,
                    10000,
                    5000,
                ),
            )


def test_detalle_rechaza_nominal_debe_y_haber_simultaneos():
    """Valida que una linea no pueda tener nominal debe y haber a la vez."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)
        asiento_id = _crear_asiento_base(db, ejercicio_id)
        cuenta = _cuenta_imputable(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO asientos_contables_detalle (
                    asiento_id,
                    renglon,
                    cuenta_contable_codigo,
                    moneda_codigo,
                    cotizacion_fecha,
                    nominal_debe_centavos,
                    nominal_haber_centavos,
                    debe_centavos
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asiento_id,
                    1,
                    cuenta,
                    "ARS",
                    "2026-06-10",
                    10000,
                    5000,
                    10000,
                ),
            )


def test_detalle_rechaza_linea_en_cero():
    """Valida que una linea no pueda quedar sin importe."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)
        asiento_id = _crear_asiento_base(db, ejercicio_id)
        cuenta = _cuenta_imputable(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO asientos_contables_detalle (
                    asiento_id,
                    renglon,
                    cuenta_contable_codigo,
                    cotizacion_fecha
                )
                VALUES (?, ?, ?, ?)
                """,
                (asiento_id, 1, cuenta, "2026-06-10"),
            )


def test_detalle_permite_linea_ars_con_nominal_igual_contable():
    """Valida linea ARS donde nominal y contable coinciden."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)
        asiento_id = _crear_asiento_base(db, ejercicio_id)
        cuenta = _cuenta_imputable(db)

        db.execute(
            """
            INSERT INTO asientos_contables_detalle (
                asiento_id,
                renglon,
                cuenta_contable_codigo,
                moneda_codigo,
                cotizacion_fecha,
                cotizacion_1000000,
                nominal_debe_centavos,
                debe_centavos
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asiento_id,
                1,
                cuenta,
                "ARS",
                "2026-06-10",
                1000000,
                12500000,
                12500000,
            ),
        )

        fila = db.execute(
            """
            SELECT moneda_codigo,
                   cotizacion_1000000,
                   nominal_debe_centavos,
                   debe_centavos,
                   nominal_haber_centavos,
                   haber_centavos
            FROM asientos_contables_detalle
            WHERE asiento_id = ?
              AND renglon = ?
            """,
            (asiento_id, 1),
        ).fetchone()

    assert fila["moneda_codigo"] == "ARS"
    assert fila["cotizacion_1000000"] == 1000000
    assert fila["nominal_debe_centavos"] == 12500000
    assert fila["debe_centavos"] == 12500000
    assert fila["nominal_haber_centavos"] == 0
    assert fila["haber_centavos"] == 0


def test_detalle_permite_linea_usd_con_nominal_y_ars_contable():
    """Valida linea USD con nominal USD y contabilidad en ARS."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)
        cotizacion_id = _crear_cotizacion_usd_ars(db)
        asiento_id = _crear_asiento_base(
            db,
            ejercicio_id,
            moneda_origen_codigo="USD",
            moneda_destino_codigo="ARS",
            cotizacion_id=cotizacion_id,
            cotizacion_1000000=1250500000,
        )
        cuenta = _cuenta_imputable(db)

        db.execute(
            """
            INSERT INTO asientos_contables_detalle (
                asiento_id,
                renglon,
                cuenta_contable_codigo,
                moneda_codigo,
                cotizacion_id,
                cotizacion_fecha,
                cotizacion_tipo,
                cotizacion_1000000,
                nominal_debe_centavos,
                debe_centavos
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asiento_id,
                1,
                cuenta,
                "USD",
                cotizacion_id,
                "2026-06-10",
                "CIERRE",
                1250500000,
                10000,
                12505000,
            ),
        )

        fila = db.execute(
            """
            SELECT moneda_codigo,
                   cotizacion_id,
                   cotizacion_1000000,
                   nominal_debe_centavos,
                   debe_centavos
            FROM asientos_contables_detalle
            WHERE asiento_id = ?
              AND renglon = ?
            """,
            (asiento_id, 1),
        ).fetchone()

    assert fila["moneda_codigo"] == "USD"
    assert fila["cotizacion_id"] == cotizacion_id
    assert fila["cotizacion_1000000"] == 1250500000
    assert fila["nominal_debe_centavos"] == 10000
    assert fila["debe_centavos"] == 12505000


def test_detalle_rechaza_ars_con_cotizacion_distinta_de_uno():
    """Valida que renglon ARS no use cotizacion distinta de 1."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _primer_ejercicio_id(db)
        asiento_id = _crear_asiento_base(db, ejercicio_id)
        cuenta = _cuenta_imputable(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO asientos_contables_detalle (
                    asiento_id,
                    renglon,
                    cuenta_contable_codigo,
                    moneda_codigo,
                    cotizacion_fecha,
                    cotizacion_1000000,
                    nominal_debe_centavos,
                    debe_centavos
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asiento_id,
                    1,
                    cuenta,
                    "ARS",
                    "2026-06-10",
                    1250500000,
                    12500000,
                    12500000,
                ),
            )
