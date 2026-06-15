from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def test_catalogos_fiscales_schema_y_seed_inicial():
    """Valida schema y carga inicial de catalogos fiscales comunes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        condiciones = db.execute(
            "SELECT codigo, descripcion FROM condiciones_iva ORDER BY CAST(codigo AS INTEGER)"
        ).fetchall()
        tipos = db.execute(
            "SELECT codigo, descripcion FROM tipos_documento ORDER BY CAST(codigo AS INTEGER)"
        ).fetchall()
        unidades = db.execute(
            "SELECT codigo, descripcion FROM unidades_medida ORDER BY orden"
        ).fetchall()
        bonificaciones = db.execute(
            "SELECT codigo, descripcion FROM tipos_bonificacion ORDER BY orden"
        ).fetchall()
        comprobantes = db.execute(
            "SELECT codigo, descripcion FROM tipos_comprobante ORDER BY orden"
        ).fetchall()

    assert len(condiciones) == 9
    assert ("5", "Consumidor Final") in [
        (fila["codigo"], fila["descripcion"]) for fila in condiciones
    ]
    assert ("6", "Responsable Monotributo") in [
        (fila["codigo"], fila["descripcion"]) for fila in condiciones
    ]
    assert len(tipos) == 6
    assert ("80", "CUIT") in [
        (fila["codigo"], fila["descripcion"]) for fila in tipos
    ]
    assert ("96", "DNI") in [
        (fila["codigo"], fila["descripcion"]) for fila in tipos
    ]
    assert len(unidades) == 8
    assert ("1", "kilogramos") in [
        (fila["codigo"], fila["descripcion"]) for fila in unidades
    ]
    assert ("7", "unidades") in [
        (fila["codigo"], fila["descripcion"]) for fila in unidades
    ]
    assert ("47", "mililitros") in [
        (fila["codigo"], fila["descripcion"]) for fila in unidades
    ]
    assert [(fila["codigo"], fila["descripcion"]) for fila in bonificaciones] == [
        ("1", "Porcentaje"),
        ("2", "Monto"),
    ]
    assert len(comprobantes) == 97
    assert ("001", "FACTURA A") in [
        (fila["codigo"], fila["descripcion"]) for fila in comprobantes
    ]
    assert ("201", "FACTURA DE CRÉDITO ELECTRÓNICA MiPyMEs (FCE) A") in [
        (fila["codigo"], fila["descripcion"]) for fila in comprobantes
    ]
    assert ("998", "Remito Electrónico para Azúcar, Alcohol y Subproductos -Exportación-") in [
        (fila["codigo"], fila["descripcion"]) for fila in comprobantes
    ]
