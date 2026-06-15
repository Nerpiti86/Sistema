import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.clientes_cuenta_corriente_service import (
    calcular_lectura_saldo_cliente,
    crear_movimiento_debe_cliente,
    crear_movimiento_haber_cliente,
    normalizar_id_cliente_cuenta_corriente,
    obtener_contexto_cuenta_corriente_cliente,
    obtener_movimiento_cliente_cuenta_corriente,
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


def _crear_cliente(db, razon_social="Cliente Cuenta Corriente", activo=1) -> int:
    grupo_id = _crear_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (razon_social, grupo_cliente_id, activo, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        (razon_social, grupo_id, activo, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def test_crear_movimiento_debe_cliente_normaliza_y_delega_repository():
    """Valida service para alta funcional de movimiento al DEBE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        movimiento = crear_movimiento_debe_cliente(
            {
                "cliente_id": str(cliente_id),
                "fecha": "2026-01-15",
                "tipo_movimiento": " factura ",
                "descripcion": " Factura de venta ",
                "moneda_codigo": "ars",
                "importe_centavos": "125000",
                "estado": "confirmado",
                "origen_tipo": " venta ",
                "origen_id": "9",
            }
        )

    assert movimiento["cliente_id"] == cliente_id
    assert movimiento["tipo_movimiento"] == "FACTURA"
    assert movimiento["descripcion"] == "Factura de venta"
    assert movimiento["moneda_codigo"] == "ARS"
    assert movimiento["debe_centavos"] == 125000
    assert movimiento["haber_centavos"] == 0
    assert movimiento["lado"] == "DEBE"
    assert movimiento["estado"] == "CONFIRMADO"
    assert movimiento["origen_tipo"] == "VENTA"
    assert movimiento["origen_id"] == 9


def test_crear_movimiento_haber_cliente_normaliza_y_delega_repository():
    """Valida service para alta funcional de movimiento al HABER."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        movimiento = crear_movimiento_haber_cliente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-16",
                "tipo_movimiento": "anticipo",
                "descripcion": " Cobranza sin factura ",
                "importe_centavos": 80000,
                "estado": "CONFIRMADO",
                "origen_tipo": "cobranza",
                "origen_id": 3,
            }
        )

    assert movimiento["tipo_movimiento"] == "ANTICIPO"
    assert movimiento["debe_centavos"] == 0
    assert movimiento["haber_centavos"] == 80000
    assert movimiento["lado"] == "HABER"
    assert movimiento["origen_tipo"] == "COBRANZA"


def test_service_rechaza_tipo_debe_en_movimiento_haber():
    """Valida que FACTURA no pueda crearse por el helper HABER."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="HABER"):
            crear_movimiento_haber_cliente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-15",
                    "tipo_movimiento": "FACTURA",
                    "descripcion": "Factura mal ubicada",
                    "importe_centavos": 100000,
                }
            )


def test_service_rechaza_tipo_haber_en_movimiento_debe():
    """Valida que ANTICIPO no pueda crearse por el helper DEBE."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="DEBE"):
            crear_movimiento_debe_cliente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-15",
                    "tipo_movimiento": "ANTICIPO",
                    "descripcion": "Anticipo mal ubicado",
                    "importe_centavos": 100000,
                }
            )


def test_service_rechaza_cliente_inactivo_para_alta_movimiento():
    """Valida regla funcional de cliente activo para nuevos movimientos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db(), activo=0)

        with pytest.raises(ValueError, match="cliente no existe o no esta activo"):
            crear_movimiento_debe_cliente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-15",
                    "tipo_movimiento": "FACTURA",
                    "descripcion": "Factura cliente inactivo",
                    "importe_centavos": 100000,
                }
            )


def test_service_rechaza_importe_no_positivo():
    """Valida importe funcional positivo en centavos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="importe"):
            crear_movimiento_debe_cliente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-15",
                    "tipo_movimiento": "FACTURA",
                    "descripcion": "Factura sin importe",
                    "importe_centavos": 0,
                }
            )


def test_service_rechaza_origen_incompleto():
    """Valida que origen_tipo y origen_id se informen juntos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="origen"):
            crear_movimiento_debe_cliente(
                {
                    "cliente_id": cliente_id,
                    "fecha": "2026-01-15",
                    "tipo_movimiento": "FACTURA",
                    "descripcion": "Origen incompleto",
                    "importe_centavos": 100000,
                    "origen_tipo": "VENTA",
                }
            )


def test_obtener_contexto_cuenta_corriente_cliente_devuelve_movimientos_y_lectura():
    """Valida contexto service sin persistir saldo propio."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        crear_movimiento_debe_cliente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-15",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura confirmada",
                "importe_centavos": 150000,
                "estado": "CONFIRMADO",
            }
        )
        crear_movimiento_haber_cliente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-16",
                "tipo_movimiento": "COBRANZA",
                "descripcion": "Cobranza confirmada",
                "importe_centavos": 50000,
                "estado": "CONFIRMADO",
            }
        )

        contexto = obtener_contexto_cuenta_corriente_cliente(cliente_id)

    assert contexto["cliente"]["id"] == cliente_id
    assert contexto["cantidad_movimientos"] == 2
    assert contexto["lectura_saldo"] == {
        "cliente_id": cliente_id,
        "total_debe_centavos": 150000,
        "total_haber_centavos": 50000,
        "saldo_centavos": 100000,
    }


def test_obtener_contexto_cuenta_corriente_cliente_filtra_estado():
    """Valida filtro funcional de estado para contexto de movimientos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        crear_movimiento_debe_cliente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-15",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura borrador",
                "importe_centavos": 100000,
                "estado": "BORRADOR",
            }
        )
        crear_movimiento_debe_cliente(
            {
                "cliente_id": cliente_id,
                "fecha": "2026-01-16",
                "tipo_movimiento": "FACTURA",
                "descripcion": "Factura confirmada",
                "importe_centavos": 100000,
                "estado": "CONFIRMADO",
            }
        )

        contexto = obtener_contexto_cuenta_corriente_cliente(
            cliente_id,
            estado="CONFIRMADO",
        )

    assert contexto["estado_filtro"] == "CONFIRMADO"
    assert contexto["cantidad_movimientos"] == 1
    assert contexto["movimientos"][0]["descripcion"] == "Factura confirmada"


def test_calcular_lectura_saldo_cliente_rechaza_cliente_inexistente():
    """Valida error funcional para cliente inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe el cliente"):
            calcular_lectura_saldo_cliente(999)


def test_obtener_movimiento_cliente_cuenta_corriente_rechaza_inexistente():
    """Valida error funcional para movimiento inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe el movimiento"):
            obtener_movimiento_cliente_cuenta_corriente(999)


def test_normalizar_id_cliente_cuenta_corriente_rechaza_invalido():
    """Valida normalizacion de id de cliente en service."""
    with pytest.raises(ValueError, match="numerico"):
        normalizar_id_cliente_cuenta_corriente("abc")

    with pytest.raises(ValueError, match="positivo"):
        normalizar_id_cliente_cuenta_corriente("0")
