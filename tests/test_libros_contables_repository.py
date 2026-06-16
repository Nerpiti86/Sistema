from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.libros_contables_repository import (
    listar_movimientos_libro_diario,
)


CUENTA_DEUDORES = "1.1.03.01.996"
CUENTA_INGRESOS = "4.1.01.01.996"


def _crear_ejercicio(db) -> int:
    fila = db.execute(
        """
        SELECT id
        FROM ejercicios_contables
        WHERE codigo = ?
        LIMIT 1
        """,
        ("2026",),
    ).fetchone()

    if fila is not None:
        return int(fila["id"])

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
            "Ejercicio libro diario",
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
    estado: str = "CONFIRMADO",
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
            estado,
            "MANUAL",
            "ARS",
            "ARS",
            fecha,
            "CIERRE",
            1000000,
            f"{fecha} 10:00:00",
            f"{fecha} 10:00:00" if estado == "CONFIRMADO" else None,
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
            "Detalle libro diario",
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


def _crear_datos_libro_diario(db) -> int:
    ejercicio_id = _crear_ejercicio(db)
    _crear_cuenta(db, CUENTA_DEUDORES, "Deudores por ventas LD", "DEBE")
    _crear_cuenta(db, CUENTA_INGRESOS, "Ingresos por servicios LD", "HABER")

    asiento_confirmado = _crear_asiento(
        db,
        ejercicio_id,
        numero_asiento=7,
        fecha="2026-06-16",
        descripcion="Comprobante: FC C 0001-00000001 | Sujeto: Cliente LD",
    )
    _crear_detalle(
        db,
        asiento_confirmado,
        renglon=1,
        cuenta=CUENTA_DEUDORES,
        debe_centavos=3500000,
        haber_centavos=0,
    )
    _crear_detalle(
        db,
        asiento_confirmado,
        renglon=2,
        cuenta=CUENTA_INGRESOS,
        debe_centavos=0,
        haber_centavos=3500000,
    )

    asiento_borrador = _crear_asiento(
        db,
        ejercicio_id,
        numero_asiento=8,
        fecha="2026-06-17",
        descripcion="Comprobante: BORRADOR | Sujeto: Cliente LD",
        estado="BORRADOR",
    )
    _crear_detalle(
        db,
        asiento_borrador,
        renglon=1,
        cuenta=CUENTA_DEUDORES,
        debe_centavos=100000,
        haber_centavos=0,
    )
    _crear_detalle(
        db,
        asiento_borrador,
        renglon=2,
        cuenta=CUENTA_INGRESOS,
        debe_centavos=0,
        haber_centavos=100000,
    )

    return ejercicio_id


def test_repository_libro_diario_lista_movimientos_confirmados_por_rango():
    """
    Valida la lectura base del Libro Diario.

    El repository debe devolver renglones contables planos, con datos de asiento
    y nombre de cuenta, sin agrupar ni formatear importes.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_datos_libro_diario(db)

        movimientos = listar_movimientos_libro_diario(
            ejercicio_id,
            "2026-06-01",
            "2026-06-30",
        )

    assert len(movimientos) == 2
    assert [movimiento["renglon"] for movimiento in movimientos] == [1, 2]
    assert movimientos[0]["numero_asiento"] == 7
    assert movimientos[0]["fecha"] == "2026-06-16"
    assert movimientos[0]["cuenta_contable_codigo"] == CUENTA_DEUDORES
    assert movimientos[0]["cuenta_nombre"] == "Deudores por ventas LD"
    assert movimientos[0]["debe_centavos"] == 3500000
    assert movimientos[0]["haber_centavos"] == 0
    assert movimientos[1]["cuenta_contable_codigo"] == CUENTA_INGRESOS
    assert movimientos[1]["cuenta_nombre"] == "Ingresos por servicios LD"
    assert movimientos[1]["debe_centavos"] == 0
    assert movimientos[1]["haber_centavos"] == 3500000


def test_repository_libro_diario_permite_filtrar_estado_borrador():
    """Valida filtro de estado para futuras vistas de control."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_datos_libro_diario(db)

        movimientos = listar_movimientos_libro_diario(
            ejercicio_id,
            "2026-06-01",
            "2026-06-30",
            "BORRADOR",
        )

    assert len(movimientos) == 2
    assert {movimiento["estado"] for movimiento in movimientos} == {"BORRADOR"}


def test_repository_libro_diario_valida_rango_de_fechas():
    """Valida que el repository rechace rango de fechas invertido."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)

        try:
            listar_movimientos_libro_diario(
                ejercicio_id,
                "2026-07-01",
                "2026-06-01",
            )
        except ValueError as exc:
            error = str(exc)
        else:
            error = ""

    assert error == "La fecha desde no puede ser posterior a la fecha hasta."
