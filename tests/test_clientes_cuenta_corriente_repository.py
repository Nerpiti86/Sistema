import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.clientes_cuenta_corriente_repository import (
    calcular_saldo_cliente_cuenta_corriente,
    crear_movimiento_cliente_cuenta_corriente,
    listar_movimientos_cliente_cuenta_corriente,
    obtener_movimiento_cliente_cuenta_corriente_por_id,
)


def _crear_grupo_cliente(db) -> int:
    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("General", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cliente(db, razon_social="Cliente Cuenta Corriente") -> int:
    grupo_id = _crear_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (razon_social, grupo_cliente_id, creado_en)
        VALUES (?, ?, ?)
        """,
        (razon_social, grupo_id, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def test_crear_movimiento_debe_devuelve_fila_normalizada():
    """Valida alta repository de movimiento DEBE con origen trazable."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        movimiento = crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": str(cliente_id),
                "fecha": "2026-01-15",
                "tipo_movimiento": "factura",
                "descripcion": " Factura de venta ",
                "moneda_codigo": "ars",
                "debe_centavos": "150000",
                "haber_centavos": 0,
                "estado": "confirmado",
                "origen_tipo": " venta ",
                "origen_id": "7",
            }
        )

    assert movimiento["id"] > 0
    assert movimiento["cliente_id"] == cliente_id
    assert movimiento["cliente_razon_social"] == "Cliente Cuenta Corriente"
    assert movimiento["fecha"] == "2026-01-15"
    assert movimiento["tipo_movimiento"] == "FACTURA"
    assert movimiento["descripcion"] == "Factura de venta"
    assert movimiento["moneda_codigo"] == "ARS"
    assert movimiento["debe_centavos"] == 150000
    assert movimiento["haber_centavos"] == 0
    assert movimiento["lado"] == "DEBE"
    assert movimiento["importe_centavos"] == 150000
    assert movimiento["estado"] == "CONFIRMADO"
    assert movimiento["esta_confirmado"] is True
    assert movimiento["origen_tipo"] == "VENTA"
    assert movimiento["origen_id"] == 7
    assert movimiento["confirmado_en"] is not None
    assert movimiento["anulado_en"] is None


def test_crear_movimiento_haber_anticipo_devuelve_fila_normalizada():
    """Valida alta repository de movimiento HABER por anticipo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        movimiento = crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-16",
                "tipo_movimiento": "ANTICIPO",
                "descripcion": "Cobranza sin factura",
                "moneda_codigo": "ARS",
                "debe_centavos": 0,
                "haber_centavos": 50000,
                "estado": "CONFIRMADO",
                "origen_tipo": "COBRANZA",
                "origen_id": 3,
            }
        )

    assert movimiento["debe_centavos"] == 0
    assert movimiento["haber_centavos"] == 50000
    assert movimiento["lado"] == "HABER"
    assert movimiento["importe_centavos"] == 50000
    assert movimiento["origen_tipo"] == "COBRANZA"
    assert movimiento["origen_id"] == 3


def test_obtener_movimiento_por_id_devuelve_none_si_no_existe():
    """Valida busqueda nula por id inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        movimiento = obtener_movimiento_cliente_cuenta_corriente_por_id(999)

    assert movimiento is None


def test_listar_movimientos_cliente_ordena_por_fecha_e_id():
    """Valida listado cronologico de movimientos por cliente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-20",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura posterior",
                "debe_centavos": 200000,
                "haber_centavos": 0,
            }
        )
        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-10",
                "tipo_movimiento": "ANTICIPO",
                "descripcion": "Anticipo anterior",
                "debe_centavos": 0,
                "haber_centavos": 50000,
            }
        )

        movimientos = listar_movimientos_cliente_cuenta_corriente(cliente_id)

    assert [movimiento["descripcion"] for movimiento in movimientos] == [
        "Anticipo anterior",
        "Factura posterior",
    ]


def test_listar_movimientos_cliente_filtra_estado():
    """Valida filtro opcional de estado en listado de movimientos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-10",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura borrador",
                "debe_centavos": 100000,
                "haber_centavos": 0,
                "estado": "BORRADOR",
            }
        )
        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-11",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura confirmada",
                "debe_centavos": 200000,
                "haber_centavos": 0,
                "estado": "CONFIRMADO",
            }
        )

        movimientos = listar_movimientos_cliente_cuenta_corriente(
            cliente_id,
            estado="CONFIRMADO",
        )

    assert len(movimientos) == 1
    assert movimientos[0]["descripcion"] == "Factura confirmada"


def test_calcular_saldo_cliente_usa_confirmados_por_defecto():
    """Valida lectura calculada de saldo sin persistir saldo en tabla."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-10",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura confirmada",
                "debe_centavos": 150000,
                "haber_centavos": 0,
                "estado": "CONFIRMADO",
            }
        )
        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-11",
                "tipo_movimiento": "COBRANZA",
                "descripcion": "Cobranza confirmada",
                "debe_centavos": 0,
                "haber_centavos": 40000,
                "estado": "CONFIRMADO",
            }
        )
        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-12",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura borrador",
                "debe_centavos": 999999,
                "haber_centavos": 0,
                "estado": "BORRADOR",
            }
        )

        saldo = calcular_saldo_cliente_cuenta_corriente(cliente_id)

    assert saldo == {
        "cliente_id": cliente_id,
        "total_debe_centavos": 150000,
        "total_haber_centavos": 40000,
        "saldo_centavos": 110000,
    }


def test_calcular_saldo_cliente_puede_incluir_todos_los_estados():
    """Valida lectura calculada incluyendo BORRADOR si el caller lo pide."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-10",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura confirmada",
                "debe_centavos": 100000,
                "haber_centavos": 0,
                "estado": "CONFIRMADO",
            }
        )
        crear_movimiento_cliente_cuenta_corriente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-11",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura borrador",
                "debe_centavos": 50000,
                "haber_centavos": 0,
                "estado": "BORRADOR",
            }
        )

        saldo = calcular_saldo_cliente_cuenta_corriente(
            cliente_id,
            solo_confirmados=False,
        )

    assert saldo["total_debe_centavos"] == 150000
    assert saldo["total_haber_centavos"] == 0
    assert saldo["saldo_centavos"] == 150000


def test_crear_movimiento_rechaza_importe_en_dos_lados():
    """Valida que repository no permita DEBE y HABER simultaneos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="DEBE o HABER"):
            crear_movimiento_cliente_cuenta_corriente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-10",
                    "tipo_movimiento": "AJUSTE",
                    "descripcion": "Movimiento invalido",
                    "debe_centavos": 100000,
                    "haber_centavos": 100000,
                }
            )


def test_crear_movimiento_rechaza_importe_cero():
    """Valida que repository exija importe positivo en un solo lado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="DEBE o HABER"):
            crear_movimiento_cliente_cuenta_corriente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-10",
                    "tipo_movimiento": "AJUSTE",
                    "descripcion": "Movimiento sin importe",
                    "debe_centavos": 0,
                    "haber_centavos": 0,
                }
            )


def test_crear_movimiento_rechaza_origen_incompleto():
    """Valida que repository exija origen_tipo y origen_id juntos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="origen"):
            crear_movimiento_cliente_cuenta_corriente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-10",
                    "tipo_movimiento": "FACTURA",
                    "descripcion": "Origen incompleto",
                    "debe_centavos": 100000,
                    "haber_centavos": 0,
                    "origen_tipo": "VENTA",
                }
            )


def test_crear_movimiento_rechaza_cliente_inexistente():
    """Valida FK contra cliente existente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_movimiento_cliente_cuenta_corriente(
                {
                    "cliente_id": 999,
                    "fecha": "2026-01-10",
                    "tipo_movimiento": "FACTURA",
                    "descripcion": "Cliente inexistente",
                    "debe_centavos": 100000,
                    "haber_centavos": 0,
                }
            )


def test_crear_movimiento_rechaza_tipo_invalido():
    """Valida tipos cerrados de movimientos de cuenta corriente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="tipo de movimiento"):
            crear_movimiento_cliente_cuenta_corriente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-10",
                    "tipo_movimiento": "VENTA_GENERICA",
                    "descripcion": "Tipo invalido",
                    "debe_centavos": 100000,
                    "haber_centavos": 0,
                }
            )
