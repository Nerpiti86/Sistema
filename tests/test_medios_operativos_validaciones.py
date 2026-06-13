from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.shared.medios_operativos_service import crear_medio_operativo_desde_formulario


def test_medio_operativo_no_banco_limpia_campos_bancarios():
    """Valida normalizacion server-side de campos bancarios no aplicables."""
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
                "banco_codigo": "65",
                "plaza": "Rosario",
                "sucursal": "Centro",
                "numero_cuenta": "123456",
                "cuit": "30-00000000-0",
                "activo": "1",
                "orden": "10",
            }
        )

    assert medio["banco_codigo"] is None
    assert medio["plaza"] is None
    assert medio["sucursal"] is None
    assert medio["numero_cuenta"] is None
    assert medio["cuit"] is None


def test_medio_operativo_ars_limpia_cambio_y_cotizacion():
    """Valida que ARS no permita cambio ni cotizacion default."""
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
                "requiere_cotizacion": "1",
                "cotizacion_default_centavos": "125050",
                "activo": "1",
                "orden": "10",
            }
        )

    assert medio["requiere_cotizacion"] == 0
    assert medio["usa_cotizacion"] is False
    assert medio["cotizacion_default_centavos"] is None


def test_medio_operativo_sin_cambio_limpia_cotizacion_default():
    """Valida que cotizacion default solo quede si cambio esta habilitado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        _insertar_cuenta_prueba("1.1.01.02.001", "Caja USD")
        medio = crear_medio_operativo_desde_formulario(
            {
                "codigo": "2",
                "nombre": "Caja dolares",
                "tipo": "EFECTIVO",
                "moneda_codigo": "USD",
                "cuenta_contable_codigo": "1.1.01.02.001",
                "cotizacion_default_centavos": "125050",
                "activo": "1",
                "orden": "20",
            }
        )

    assert medio["requiere_cotizacion"] == 0
    assert medio["cotizacion_default_centavos"] is None


def _insertar_cuenta_prueba(
    cuenta="1.1.01.01.001",
    descripcion="Caja ARS",
):
    from app.db import get_db

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
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )
