from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.libros_contables_repository import (
    listar_saldos_mayor_general,
)


CUENTA_DEBE = "1.1.03.01.993"
CUENTA_HABER = "4.1.01.01.993"


def _crear_ejercicio(db) -> int:
    cursor = db.execute(
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
            "2093",
            "Ejercicio mayor general",
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
    return int(cursor.lastrowid)


def _crear_cuenta(db, cuenta: str, descripcion: str, saldo_habitual: str) -> None:
    db.execute(
        """
        INSERT OR IGNORE INTO cuentas_contables (
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
            saldo_habitual,
            "PATRIMONIAL" if saldo_habitual == "DEBE" else "RESULTADO",
            1,
            1 if saldo_habitual == "DEBE" else 0,
            "2026-01-01 00:00:00",
        ),
    )
    db.execute(
        """
        UPDATE cuentas_contables
        SET descripcion = ?,
            saldo_habitual = ?
        WHERE cuenta = ?
        """,
        (descripcion, saldo_habitual, cuenta),
    )


def _crear_asiento(
    db,
    ejercicio_id: int,
    *,
    numero_asiento: int,
    fecha: str,
    descripcion: str,
) -> int:
    cursor = db.execute(
        """
        INSERT INTO asientos_contables (
            ejercicio_id,
            numero_asiento,
            fecha,
            descripcion,
            estado,
            tipo,
            moneda_origen_codigo,
            moneda_destino_codigo,
            cotizacion_fecha,
            cotizacion_tipo,
            cotizacion_1000000,
            creado_en,
            confirmado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ejercicio_id,
            numero_asiento,
            fecha,
            descripcion,
            "CONFIRMADO",
            "MANUAL",
            "ARS",
            "ARS",
            fecha,
            "CIERRE",
            1000000,
            f"{fecha} 10:00:00",
            f"{fecha} 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _crear_detalle(
    db,
    asiento_id: int,
    *,
    renglon: int,
    cuenta: str,
    debe_centavos: int,
    haber_centavos: int,
) -> None:
    db.execute(
        """
        INSERT INTO asientos_contables_detalle (
            asiento_id,
            renglon,
            cuenta_contable_codigo,
            descripcion,
            moneda_codigo,
            cotizacion_fecha,
            cotizacion_tipo,
            cotizacion_1000000,
            nominal_debe_centavos,
            nominal_haber_centavos,
            debe_centavos,
            haber_centavos
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asiento_id,
            renglon,
            cuenta,
            "Detalle mayor general",
            "ARS",
            "2026-06-16",
            "CIERRE",
            1000000,
            debe_centavos,
            haber_centavos,
            debe_centavos,
            haber_centavos,
        ),
    )


def _crear_datos_mayor_general(db) -> int:
    ejercicio_id = _crear_ejercicio(db)
    _crear_cuenta(db, CUENTA_DEBE, "Deudores mayor general", "DEBE")
    _crear_cuenta(db, CUENTA_HABER, "Ingresos mayor general", "HABER")

    asiento_inicial = _crear_asiento(
        db,
        ejercicio_id,
        numero_asiento=1,
        fecha="2026-05-31",
        descripcion="Comprobante: SI | Sujeto: Inicial",
    )
    _crear_detalle(
        db,
        asiento_inicial,
        renglon=1,
        cuenta=CUENTA_DEBE,
        debe_centavos=1000000,
        haber_centavos=0,
    )
    _crear_detalle(
        db,
        asiento_inicial,
        renglon=2,
        cuenta=CUENTA_HABER,
        debe_centavos=0,
        haber_centavos=1000000,
    )

    asiento_periodo = _crear_asiento(
        db,
        ejercicio_id,
        numero_asiento=2,
        fecha="2026-06-16",
        descripcion="Comprobante: FC C 0001-00000001 | Sujeto: Cliente mayor",
    )
    _crear_detalle(
        db,
        asiento_periodo,
        renglon=1,
        cuenta=CUENTA_DEBE,
        debe_centavos=3500000,
        haber_centavos=0,
    )
    _crear_detalle(
        db,
        asiento_periodo,
        renglon=2,
        cuenta=CUENTA_HABER,
        debe_centavos=0,
        haber_centavos=3500000,
    )

    asiento_posterior = _crear_asiento(
        db,
        ejercicio_id,
        numero_asiento=3,
        fecha="2026-07-01",
        descripcion="Comprobante: POST | Sujeto: Posterior",
    )
    _crear_detalle(
        db,
        asiento_posterior,
        renglon=1,
        cuenta=CUENTA_DEBE,
        debe_centavos=900000,
        haber_centavos=0,
    )
    _crear_detalle(
        db,
        asiento_posterior,
        renglon=2,
        cuenta=CUENTA_HABER,
        debe_centavos=0,
        haber_centavos=900000,
    )

    return ejercicio_id


def test_repository_mayor_general_agrega_saldos_por_cuenta():
    """Valida saldo inicial y totales del periodo por cuenta."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_datos_mayor_general(db)

        saldos = listar_saldos_mayor_general(
            ejercicio_id,
            "2026-06-01",
            "2026-06-30",
        )

    assert [saldo["cuenta_contable_codigo"] for saldo in saldos] == [
        CUENTA_DEBE,
        CUENTA_HABER,
    ]

    saldo_debe = saldos[0]
    assert saldo_debe["cuenta_nombre"] == "Deudores mayor general"
    assert saldo_debe["cuenta_saldo_habitual"] == "DEBE"
    assert saldo_debe["saldo_inicial_debe_centavos"] == 1000000
    assert saldo_debe["saldo_inicial_haber_centavos"] == 0
    assert saldo_debe["total_debe_periodo_centavos"] == 3500000
    assert saldo_debe["total_haber_periodo_centavos"] == 0

    saldo_haber = saldos[1]
    assert saldo_haber["cuenta_nombre"] == "Ingresos mayor general"
    assert saldo_haber["cuenta_saldo_habitual"] == "HABER"
    assert saldo_haber["saldo_inicial_debe_centavos"] == 0
    assert saldo_haber["saldo_inicial_haber_centavos"] == 1000000
    assert saldo_haber["total_debe_periodo_centavos"] == 0
    assert saldo_haber["total_haber_periodo_centavos"] == 3500000


def test_repository_mayor_general_valida_rango_fechas():
    """Valida rechazo de rango invertido."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)

        try:
            listar_saldos_mayor_general(
                ejercicio_id,
                "2026-07-01",
                "2026-06-01",
            )
        except ValueError as exc:
            error = str(exc)
        else:
            error = ""

    assert error == "La fecha desde no puede ser posterior a la fecha hasta."
