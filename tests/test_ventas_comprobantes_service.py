import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.ventas_comprobantes_service import (
    crear_borrador_comprobante_venta,
    listar_comprobantes_venta,
    obtener_comprobante_venta,
)


def _crear_grupo_cliente(db) -> int:
    fila_grupo = db.execute(
        """
        SELECT id
        FROM grupos_clientes
        WHERE nombre = ?
        LIMIT 1
        """,
        ("General",),
    ).fetchone()

    if fila_grupo is not None:
        return int(fila_grupo["id"])

    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("General", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cliente(db, razon_social="Cliente Venta", activo=1) -> int:
    grupo_id = _crear_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (razon_social, grupo_cliente_id, activo, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        (razon_social, grupo_id, activo, "2026-01-01 10:00:00"),
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
            "HABER",
            "RESULTADO",
            1,
            0,
            None,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def _crear_articulo_venta(
    db,
    cuenta_ingreso_codigo: str | None,
    nombre="Sesion",
    moneda_codigo="ARS",
    activo=1,
    precio_unitario_sugerido_centavos=100000,
) -> int:
    cursor = db.execute(
        """
        INSERT INTO articulos_venta (
            nombre,
            tipo,
            moneda_codigo,
            precio_unitario_sugerido_centavos,
            cuenta_ingreso_codigo,
            activo,
            orden,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nombre,
            "SERVICIO",
            moneda_codigo,
            precio_unitario_sugerido_centavos,
            cuenta_ingreso_codigo,
            activo,
            10,
            "2026-01-01 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def _datos_comprobante(cliente_id: int, numero=25) -> dict:
    return {
        "cliente_id": cliente_id,
        "fecha": "2026-01-15",
        "fecha_vencimiento": "2026-02-15",
        "tipo_comprobante": "factura",
        "letra": "x",
        "punto_venta": "1",
        "numero": str(numero),
        "moneda_codigo": "ars",
        "cotizacion_centavos": "100",
        "observaciones": " Observacion ",
    }


def _detalle(articulo_id: int) -> dict:
    return {
        "articulo_venta_id": str(articulo_id),
        "cantidad_1000000": "1000000",
        "iva_centavos": "21000",
        "orden": "1",
    }


def test_crear_borrador_comprobante_venta_copia_datos_del_articulo():
    """El service crea solo BORRADOR y copia datos historicos del articulo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        articulo_id = _crear_articulo_venta(
            db,
            cuenta_ingreso,
            nombre="Sesion de psicologia",
            precio_unitario_sugerido_centavos=100000,
        )

        comprobante = crear_borrador_comprobante_venta(
            _datos_comprobante(cliente_id),
            [_detalle(articulo_id)],
        )

    assert comprobante["estado"] == "BORRADOR"
    assert comprobante["esta_borrador"] is True
    assert comprobante["asiento_id"] is None
    assert comprobante["cliente_id"] == cliente_id
    assert comprobante["tipo_comprobante"] == "FACTURA"
    assert comprobante["letra"] == "X"
    assert comprobante["moneda_codigo"] == "ARS"
    assert comprobante["subtotal_centavos"] == 100000
    assert comprobante["descuento_centavos"] == 0
    assert comprobante["recargo_centavos"] == 0
    assert comprobante["iva_centavos"] == 21000
    assert comprobante["total_centavos"] == 121000
    assert comprobante["cantidad_detalles"] == 1
    assert comprobante["detalles"][0]["descripcion"] == "Sesion de psicologia"
    assert comprobante["detalles"][0]["precio_unitario_centavos"] == 100000
    assert comprobante["detalles"][0]["cuenta_ingreso_codigo"] == cuenta_ingreso


def test_crear_borrador_comprobante_venta_permite_descripcion_y_precio_manual():
    """El service permite precio manual pero conserva cuenta del articulo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        comprobante = crear_borrador_comprobante_venta(
            _datos_comprobante(cliente_id),
            [
                {
                    **_detalle(articulo_id),
                    "descripcion": "Consulta inicial",
                    "precio_unitario_centavos": "150000",
                    "iva_centavos": "31500",
                }
            ],
        )

    detalle = comprobante["detalles"][0]
    assert detalle["descripcion"] == "Consulta inicial"
    assert detalle["precio_unitario_centavos"] == 150000
    assert detalle["subtotal_centavos"] == 150000
    assert detalle["iva_centavos"] == 31500
    assert detalle["total_linea_centavos"] == 181500
    assert detalle["cuenta_ingreso_codigo"] == cuenta_ingreso
    assert comprobante["total_centavos"] == 181500


def test_crear_borrador_comprobante_venta_calcula_cantidad_escalada():
    """El service calcula importes con cantidad escalada en 1.000.000."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        articulo_id = _crear_articulo_venta(
            db,
            cuenta_ingreso,
            precio_unitario_sugerido_centavos=100000,
        )

        comprobante = crear_borrador_comprobante_venta(
            _datos_comprobante(cliente_id),
            [
                {
                    **_detalle(articulo_id),
                    "cantidad_1000000": "500000",
                    "iva_centavos": "10500",
                }
            ],
        )

    assert comprobante["subtotal_centavos"] == 50000
    assert comprobante["iva_centavos"] == 10500
    assert comprobante["total_centavos"] == 60500


def test_crear_borrador_comprobante_venta_suma_descuentos_de_linea_y_global():
    """El service consolida descuentos de renglones y descuento global."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        comprobante = crear_borrador_comprobante_venta(
            {
                **_datos_comprobante(cliente_id),
                "descuento_centavos": "5000",
                "recargo_centavos": "2000",
            },
            [
                {
                    **_detalle(articulo_id),
                    "descuento_centavos": "10000",
                    "iva_centavos": "18900",
                }
            ],
        )

    assert comprobante["subtotal_centavos"] == 100000
    assert comprobante["descuento_centavos"] == 15000
    assert comprobante["recargo_centavos"] == 2000
    assert comprobante["iva_centavos"] == 18900
    assert comprobante["total_centavos"] == 105900


def test_crear_borrador_comprobante_venta_rechaza_cliente_inactivo():
    """El service no permite crear ventas para clientes inactivos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db, activo=0)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        with pytest.raises(ValueError, match="cliente"):
            crear_borrador_comprobante_venta(
                _datos_comprobante(cliente_id),
                [_detalle(articulo_id)],
            )


def test_crear_borrador_comprobante_venta_rechaza_articulo_inactivo():
    """El service no permite vender articulos inactivos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso, activo=0)

        with pytest.raises(ValueError, match="no esta activo"):
            crear_borrador_comprobante_venta(
                _datos_comprobante(cliente_id),
                [_detalle(articulo_id)],
            )


def test_crear_borrador_comprobante_venta_rechaza_articulo_sin_cuenta_ingreso():
    """El service exige cuenta de ingreso para poder facturar un articulo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)
        articulo_id = _crear_articulo_venta(db, None)

        with pytest.raises(ValueError, match="cuenta de ingreso"):
            crear_borrador_comprobante_venta(
                _datos_comprobante(cliente_id),
                [_detalle(articulo_id)],
            )


def test_crear_borrador_comprobante_venta_rechaza_moneda_incompatible():
    """El service mantiene una sola moneda por comprobante."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso, moneda_codigo="USD")

        with pytest.raises(ValueError, match="moneda"):
            crear_borrador_comprobante_venta(
                _datos_comprobante(cliente_id),
                [_detalle(articulo_id)],
            )


def test_crear_borrador_comprobante_venta_rechaza_estado_confirmado():
    """El alta comercial inicial solo puede nacer en BORRADOR."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="BORRADOR"):
            crear_borrador_comprobante_venta(
                {
                    **_datos_comprobante(cliente_id),
                    "estado": "CONFIRMADO",
                },
                [],
            )


def test_crear_borrador_comprobante_venta_rechaza_sin_detalles():
    """El comprobante comercial debe tener al menos un renglon."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="renglon"):
            crear_borrador_comprobante_venta(_datos_comprobante(cliente_id), [])


def test_obtener_comprobante_venta_rechaza_inexistente():
    """El service devuelve error funcional para comprobantes inexistentes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe"):
            obtener_comprobante_venta(999)


def test_listar_comprobantes_venta_devuelve_borradores_creados():
    """El service lista comprobantes delegando al repository de ventas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)
        cliente_id = _crear_cliente(db)

        crear_borrador_comprobante_venta(
            _datos_comprobante(cliente_id),
            [_detalle(articulo_id)],
        )

        comprobantes = listar_comprobantes_venta()

    assert len(comprobantes) == 1
    assert comprobantes[0]["estado"] == "BORRADOR"


def test_service_ventas_comprobantes_no_usa_sql_ni_get_db():
    """Contrato de capas: service sin SQL directo ni get_db."""
    from pathlib import Path

    contenido = Path("app/gestion/ventas_comprobantes_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert "SELECT " not in contenido
    assert "INSERT " not in contenido
    assert "UPDATE " not in contenido
    assert "DELETE " not in contenido
