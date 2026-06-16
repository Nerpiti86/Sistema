from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.libros_contables_repository import (
    listar_movimientos_mayor_por_cuenta,
    obtener_saldo_inicial_mayor_por_cuenta,
)


CUENTA_MAYOR = "1.1.03.01.994"
CUENTA_CONTRA = "4.1.01.01.994"


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
            "2026",
            "Ejercicio mayor cuenta",
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
            "Detalle mayor cuenta",
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


def _crear_datos_mayor(db) -> int:
    ejercicio_id = _crear_ejercicio(db)
    _crear_cuenta(db, CUENTA_MAYOR, "Deudores por ventas mayor", "DEBE")
    _crear_cuenta(db, CUENTA_CONTRA, "Ingresos por servicios mayor", "HABER")

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
        cuenta=CUENTA_MAYOR,
        debe_centavos=1000000,
        haber_centavos=0,
    )
    _crear_detalle(
        db,
        asiento_inicial,
        renglon=2,
        cuenta=CUENTA_CONTRA,
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
        cuenta=CUENTA_MAYOR,
        debe_centavos=3500000,
        haber_centavos=0,
    )
    _crear_detalle(
        db,
        asiento_periodo,
        renglon=2,
        cuenta=CUENTA_CONTRA,
        debe_centavos=0,
        haber_centavos=3500000,
    )

    asiento_otro = _crear_asiento(
        db,
        ejercicio_id,
        numero_asiento=3,
        fecha="2026-06-20",
        descripcion="Comprobante: OTRO | Sujeto: Otro",
    )
    _crear_detalle(
        db,
        asiento_otro,
        renglon=1,
        cuenta=CUENTA_CONTRA,
        debe_centavos=100000,
        haber_centavos=0,
    )
    _crear_detalle(
        db,
        asiento_otro,
        renglon=2,
        cuenta=CUENTA_MAYOR,
        debe_centavos=0,
        haber_centavos=100000,
    )

    return ejercicio_id


def test_repository_mayor_por_cuenta_calcula_saldo_inicial():
    """Valida debe/haber anterior al rango para una cuenta."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_datos_mayor(db)

        saldo = obtener_saldo_inicial_mayor_por_cuenta(
            ejercicio_id,
            CUENTA_MAYOR,
            "2026-06-01",
        )

    assert saldo == {
        "debe_centavos": 1000000,
        "haber_centavos": 0,
    }


def test_repository_mayor_por_cuenta_lista_solo_cuenta_y_periodo():
    """Valida movimientos de una sola cuenta dentro del periodo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_datos_mayor(db)

        movimientos = listar_movimientos_mayor_por_cuenta(
            ejercicio_id,
            CUENTA_MAYOR,
            "2026-06-01",
            "2026-06-30",
        )

    assert len(movimientos) == 2
    assert [movimiento["numero_asiento"] for movimiento in movimientos] == [2, 3]
    assert {movimiento["cuenta_contable_codigo"] for movimiento in movimientos} == {
        CUENTA_MAYOR
    }
    assert movimientos[0]["cuenta_nombre"] == "Deudores por ventas mayor"
    assert movimientos[0]["debe_centavos"] == 3500000
    assert movimientos[0]["haber_centavos"] == 0
    assert movimientos[1]["debe_centavos"] == 0
    assert movimientos[1]["haber_centavos"] == 100000


def test_repository_mayor_por_cuenta_valida_rango_fechas():
    """Valida rechazo de rango invertido."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)

        try:
            listar_movimientos_mayor_por_cuenta(
                ejercicio_id,
                CUENTA_MAYOR,
                "2026-07-01",
                "2026-06-01",
            )
        except ValueError as exc:
            error = str(exc)
        else:
            error = ""

    assert error == "La fecha desde no puede ser posterior a la fecha hasta."
