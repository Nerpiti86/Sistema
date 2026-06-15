import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.ventas_comprobantes_repository import (
    crear_venta_comprobante,
    listar_ventas_comprobantes,
    listar_ventas_comprobantes_detalle,
    obtener_venta_comprobante_por_id,
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


def _crear_cliente(db, razon_social="Cliente Venta") -> int:
    grupo_id = _crear_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (razon_social, grupo_cliente_id, activo, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        (razon_social, grupo_id, 1, "2026-01-01 10:00:00"),
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


def _crear_articulo_venta(db, cuenta_ingreso_codigo: str, nombre="Sesion") -> int:
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
            "ARS",
            100000,
            cuenta_ingreso_codigo,
            1,
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
        "tipo_comprobante": " factura ",
        "letra": " x ",
        "punto_venta": "1",
        "numero": str(numero),
        "moneda_codigo": "ars",
        "cotizacion_centavos": "100",
        "subtotal_centavos": "100000",
        "descuento_centavos": "0",
        "recargo_centavos": "0",
        "iva_centavos": "21000",
        "total_centavos": "121000",
        "estado": "borrador",
        "observaciones": " Observacion ",
    }


def _detalle(articulo_id: int, cuenta_ingreso: str) -> dict:
    return {
        "articulo_venta_id": str(articulo_id),
        "descripcion": " Sesion de psicologia ",
        "cantidad_1000000": "1000000",
        "precio_unitario_centavos": "100000",
        "descuento_centavos": "0",
        "subtotal_centavos": "100000",
        "iva_centavos": "21000",
        "total_linea_centavos": "121000",
        "cuenta_ingreso_codigo": cuenta_ingreso,
        "orden": "1",
        "observaciones": " Linea ",
    }


def test_crear_venta_comprobante_inserta_cabecera_y_detalle_normalizados():
    """Valida alta repository del documento comercial de venta."""
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

        comprobante = crear_venta_comprobante(
            _datos_comprobante(cliente_id),
            [_detalle(articulo_id, cuenta_ingreso)],
        )

    assert comprobante["id"] > 0
    assert comprobante["cliente_id"] == cliente_id
    assert comprobante["cliente_razon_social"] == "Cliente Venta"
    assert comprobante["fecha"] == "2026-01-15"
    assert comprobante["fecha_vencimiento"] == "2026-02-15"
    assert comprobante["tipo_comprobante"] == "FACTURA"
    assert comprobante["letra"] == "X"
    assert comprobante["punto_venta"] == 1
    assert comprobante["numero"] == 25
    assert comprobante["numero_formateado"] == "X 0001-00000025"
    assert comprobante["moneda_codigo"] == "ARS"
    assert comprobante["cotizacion_centavos"] == 100
    assert comprobante["total_centavos"] == 121000
    assert comprobante["estado"] == "BORRADOR"
    assert comprobante["esta_borrador"] is True
    assert comprobante["cantidad_detalles"] == 1
    assert comprobante["detalles"][0]["descripcion"] == "Sesion de psicologia"
    assert comprobante["detalles"][0]["articulo_venta_id"] == articulo_id
    assert comprobante["detalles"][0]["cuenta_ingreso_codigo"] == cuenta_ingreso
    assert comprobante["detalles"][0]["total_linea_centavos"] == 121000


def test_obtener_venta_comprobante_por_id_devuelve_none_si_no_existe():
    """Valida busqueda nula por id inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        comprobante = obtener_venta_comprobante_por_id(999)

    assert comprobante is None


def test_listar_ventas_comprobantes_ordena_fecha_descendente():
    """Valida orden operativo del listado de comprobantes."""
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
        cliente_a = _crear_cliente(db, "Cliente A")
        cliente_b = _crear_cliente(db, "Cliente B")

        crear_venta_comprobante(
            {
                **_datos_comprobante(cliente_a, numero=1),
                "fecha": "2026-01-10",
            },
            [_detalle(articulo_id, cuenta_ingreso)],
        )
        crear_venta_comprobante(
            {
                **_datos_comprobante(cliente_b, numero=2),
                "fecha": "2026-01-20",
            },
            [_detalle(articulo_id, cuenta_ingreso)],
        )

        comprobantes = listar_ventas_comprobantes()

    assert [comprobante["cliente_razon_social"] for comprobante in comprobantes] == [
        "Cliente B",
        "Cliente A",
    ]


def test_listar_ventas_comprobantes_detalle_ordena_por_orden():
    """Valida listado ordenado de renglones por comprobante."""
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
        articulo_a = _crear_articulo_venta(db, cuenta_ingreso, "Articulo A")
        articulo_b = _crear_articulo_venta(db, cuenta_ingreso, "Articulo B")

        comprobante = crear_venta_comprobante(
            {
                **_datos_comprobante(cliente_id),
                "subtotal_centavos": 200000,
                "iva_centavos": 42000,
                "total_centavos": 242000,
            },
            [
                {
                    **_detalle(articulo_b, cuenta_ingreso),
                    "descripcion": "Linea B",
                    "subtotal_centavos": 100000,
                    "iva_centavos": 21000,
                    "total_linea_centavos": 121000,
                    "orden": 2,
                },
                {
                    **_detalle(articulo_a, cuenta_ingreso),
                    "descripcion": "Linea A",
                    "subtotal_centavos": 100000,
                    "iva_centavos": 21000,
                    "total_linea_centavos": 121000,
                    "orden": 1,
                },
            ],
        )

        detalles = listar_ventas_comprobantes_detalle(comprobante["id"])

    assert [detalle["descripcion"] for detalle in detalles] == ["Linea A", "Linea B"]


def test_crear_venta_comprobante_rechaza_sin_detalles():
    """Valida que el repository no cree comprobantes comerciales sin renglones."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="renglon"):
            crear_venta_comprobante(_datos_comprobante(cliente_id), [])


def test_crear_venta_comprobante_rechaza_total_inconsistente():
    """Valida cierre de total de cabecera antes de persistir."""
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

        with pytest.raises(ValueError, match="total"):
            crear_venta_comprobante(
                {
                    **_datos_comprobante(cliente_id),
                    "total_centavos": 100000,
                },
                [_detalle(articulo_id, cuenta_ingreso)],
            )


def test_crear_venta_comprobante_rechaza_total_linea_inconsistente():
    """Valida cierre de total de renglon antes de persistir."""
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

        with pytest.raises(ValueError, match="renglon"):
            crear_venta_comprobante(
                _datos_comprobante(cliente_id),
                [
                    {
                        **_detalle(articulo_id, cuenta_ingreso),
                        "total_linea_centavos": 100000,
                    }
                ],
            )


def test_crear_venta_comprobante_rechaza_cliente_inexistente():
    """Valida FK contra cliente existente."""
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

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_venta_comprobante(
                _datos_comprobante(999),
                [_detalle(articulo_id, cuenta_ingreso)],
            )


def test_crear_venta_comprobante_rechaza_articulo_inexistente():
    """Valida FK contra articulo de venta existente."""
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

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_venta_comprobante(
                _datos_comprobante(cliente_id),
                [_detalle(999, cuenta_ingreso)],
            )


def test_crear_venta_comprobante_rechaza_numeracion_duplicada():
    """Valida restriccion unica para comprobantes numerados."""
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

        crear_venta_comprobante(
            _datos_comprobante(cliente_id, numero=25),
            [_detalle(articulo_id, cuenta_ingreso)],
        )

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_venta_comprobante(
                _datos_comprobante(cliente_id, numero=25),
                [_detalle(articulo_id, cuenta_ingreso)],
            )


def test_crear_venta_comprobante_rechaza_tipo_invalido():
    """Valida tipos cerrados de comprobantes comerciales de venta."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente_id = _crear_cliente(get_db())

        with pytest.raises(ValueError, match="tipo"):
            crear_venta_comprobante(
                {
                    **_datos_comprobante(cliente_id),
                    "tipo_comprobante": "RECIBO",
                },
                [],
            )
