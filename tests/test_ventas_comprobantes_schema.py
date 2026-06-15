import sqlite3

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _crear_grupo_cliente(db) -> int:
    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("General", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cliente(db) -> int:
    grupo_id = _crear_grupo_cliente(db)
    cursor = db.execute(
        """
        INSERT INTO clientes (razon_social, grupo_cliente_id, activo, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        ("Cliente Venta", grupo_id, 1, "2026-01-01 10:00:00"),
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


def _crear_articulo_venta(db, cuenta_ingreso_codigo: str) -> int:
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
            "Sesion de psicologia",
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


def _crear_comprobante_venta(db, cliente_id: int) -> int:
    cursor = db.execute(
        """
        INSERT INTO ventas_comprobantes (
            cliente_id,
            fecha,
            fecha_vencimiento,
            tipo_comprobante,
            tipo_comprobante_codigo,
            letra,
            punto_venta,
            numero,
            moneda_codigo,
            cotizacion_centavos,
            subtotal_centavos,
            descuento_centavos,
            recargo_centavos,
            iva_centavos,
            total_centavos,
            estado,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cliente_id,
            "2026-01-15",
            "2026-02-15",
            "FACTURA",
            "011",
            "X",
            1,
            25,
            "ARS",
            100,
            100000,
            0,
            0,
            21000,
            121000,
            "BORRADOR",
            "2026-01-15 10:00:00",
        ),
    )
    return int(cursor.lastrowid)


def test_migracion_crea_tablas_ventas_comprobantes_y_detalle():
    """
    Contrato: ventas nace como documento comercial separado de cobranzas y fondos.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cabecera = db.execute("PRAGMA table_info(ventas_comprobantes)").fetchall()
        detalle = db.execute("PRAGMA table_info(ventas_comprobantes_detalle)").fetchall()

    columnas_cabecera = {columna["name"] for columna in cabecera}
    columnas_detalle = {columna["name"] for columna in detalle}

    assert {
        "id",
        "cliente_id",
        "fecha",
        "fecha_vencimiento",
        "tipo_comprobante",
        "tipo_comprobante_codigo",
        "letra",
        "punto_venta",
        "numero",
        "moneda_codigo",
        "cotizacion_centavos",
        "subtotal_centavos",
        "descuento_centavos",
        "recargo_centavos",
        "iva_centavos",
        "total_centavos",
        "estado",
        "asiento_id",
        "observaciones",
        "creado_en",
        "actualizado_en",
        "confirmado_en",
        "anulado_en",
    }.issubset(columnas_cabecera)

    assert {
        "id",
        "comprobante_id",
        "articulo_venta_id",
        "descripcion",
        "cantidad_1000000",
        "unidad_medida_codigo",
        "precio_unitario_centavos",
        "tipo_bonificacion_codigo",
        "bonificacion_valor_10000",
        "descuento_centavos",
        "subtotal_centavos",
        "iva_centavos",
        "total_linea_centavos",
        "cuenta_ingreso_codigo",
        "orden",
        "observaciones",
    }.issubset(columnas_detalle)

    assert "saldo_centavos" not in columnas_cabecera
    assert "cobrado_centavos" not in columnas_cabecera
    assert "medio_pago_id" not in columnas_cabecera
    assert "banco_id" not in columnas_cabecera


def test_ventas_comprobantes_permite_factura_borrador_con_total_consistente():
    """
    Contrato: una factura se guarda como cabecera comercial, sin mover fondos.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        comprobante_id = _crear_comprobante_venta(db, cliente_id)

        comprobante = db.execute(
            """
            SELECT tipo_comprobante, tipo_comprobante_codigo, total_centavos, estado
            FROM ventas_comprobantes
            WHERE id = ?
            """,
            (comprobante_id,),
        ).fetchone()

    assert comprobante["tipo_comprobante"] == "FACTURA"
    assert comprobante["tipo_comprobante_codigo"] == "011"
    assert comprobante["total_centavos"] == 121000
    assert comprobante["estado"] == "BORRADOR"


def test_ventas_comprobantes_permite_detalle_con_articulo_y_cuenta_copiada():
    """
    Contrato: el detalle copia descripcion, precio y cuenta del articulo al vender.
    """
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
        comprobante_id = _crear_comprobante_venta(db, cliente_id)

        db.execute(
            """
            INSERT INTO ventas_comprobantes_detalle (
                comprobante_id,
                articulo_venta_id,
                descripcion,
                cantidad_1000000,
                precio_unitario_centavos,
                descuento_centavos,
                subtotal_centavos,
                iva_centavos,
                total_linea_centavos,
                cuenta_ingreso_codigo,
                orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                comprobante_id,
                articulo_id,
                "Sesion de psicologia",
                1000000,
                100000,
                0,
                100000,
                21000,
                121000,
                cuenta_ingreso,
                1,
            ),
        )

        detalle = db.execute(
            """
            SELECT descripcion, total_linea_centavos, cuenta_ingreso_codigo
            FROM ventas_comprobantes_detalle
            WHERE comprobante_id = ?
            """,
            (comprobante_id,),
        ).fetchone()

    assert detalle["descripcion"] == "Sesion de psicologia"
    assert detalle["total_linea_centavos"] == 121000
    assert detalle["cuenta_ingreso_codigo"] == cuenta_ingreso


def test_ventas_comprobantes_rechaza_total_inconsistente():
    """
    Contrato: el total de cabecera debe cerrar con subtotal, descuentos, recargos e IVA.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ventas_comprobantes (
                    cliente_id,
                    fecha,
                    tipo_comprobante,
                    subtotal_centavos,
                    descuento_centavos,
                    recargo_centavos,
                    iva_centavos,
                    total_centavos,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente_id,
                    "2026-01-15",
                    "FACTURA",
                    100000,
                    0,
                    0,
                    21000,
                    100000,
                    "2026-01-15 10:00:00",
                ),
            )


def test_ventas_comprobantes_rechaza_tipo_invalido():
    """
    Contrato: los tipos comerciales deben coincidir con cuenta corriente.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ventas_comprobantes (
                    cliente_id,
                    fecha,
                    tipo_comprobante,
                    subtotal_centavos,
                    total_centavos,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente_id,
                    "2026-01-15",
                    "RECIBO",
                    100000,
                    100000,
                    "2026-01-15 10:00:00",
                ),
            )


def test_ventas_comprobantes_rechaza_fk_cliente_inexistente():
    """
    Contrato: todo comprobante de venta pertenece a un cliente existente.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                """
                INSERT INTO ventas_comprobantes (
                    cliente_id,
                    fecha,
                    tipo_comprobante,
                    subtotal_centavos,
                    total_centavos,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    999,
                    "2026-01-15",
                    "FACTURA",
                    100000,
                    100000,
                    "2026-01-15 10:00:00",
                ),
            )


def test_ventas_comprobantes_rechaza_numero_duplicado_si_es_real():
    """
    Contrato: tipo/letra/punto_venta/numero identifica un comprobante numerado.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        _crear_comprobante_venta(db, cliente_id)

        with pytest.raises(sqlite3.IntegrityError):
            _crear_comprobante_venta(db, cliente_id)


def test_ventas_comprobantes_detalle_rechaza_total_linea_inconsistente():
    """
    Contrato: cada renglon debe cerrar subtotal - descuento + IVA.
    """
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
        comprobante_id = _crear_comprobante_venta(db, cliente_id)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ventas_comprobantes_detalle (
                    comprobante_id,
                    articulo_venta_id,
                    descripcion,
                    cantidad_1000000,
                    precio_unitario_centavos,
                    descuento_centavos,
                    subtotal_centavos,
                    iva_centavos,
                    total_linea_centavos,
                    cuenta_ingreso_codigo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comprobante_id,
                    articulo_id,
                    "Detalle inconsistente",
                    1000000,
                    100000,
                    0,
                    100000,
                    21000,
                    100000,
                    cuenta_ingreso,
                ),
            )


def test_ventas_comprobantes_detalle_rechaza_articulo_inexistente():
    """
    Contrato: cada renglon referencia un articulo de venta existente.
    """
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
        comprobante_id = _crear_comprobante_venta(db, cliente_id)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ventas_comprobantes_detalle (
                    comprobante_id,
                    articulo_venta_id,
                    descripcion,
                    cantidad_1000000,
                    precio_unitario_centavos,
                    subtotal_centavos,
                    iva_centavos,
                    total_linea_centavos,
                    cuenta_ingreso_codigo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comprobante_id,
                    999,
                    "Articulo inexistente",
                    1000000,
                    100000,
                    100000,
                    21000,
                    121000,
                    cuenta_ingreso,
                ),
            )


def test_ventas_comprobantes_detalle_rechaza_cuenta_ingreso_inexistente():
    """
    Contrato: el renglon conserva cuenta contable de ingreso valida.
    """
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
        comprobante_id = _crear_comprobante_venta(db, cliente_id)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ventas_comprobantes_detalle (
                    comprobante_id,
                    articulo_venta_id,
                    descripcion,
                    cantidad_1000000,
                    precio_unitario_centavos,
                    subtotal_centavos,
                    iva_centavos,
                    total_linea_centavos,
                    cuenta_ingreso_codigo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comprobante_id,
                    articulo_id,
                    "Cuenta inexistente",
                    1000000,
                    100000,
                    100000,
                    21000,
                    121000,
                    "4.1.01.01.998",
                ),
            )


def test_ventas_comprobantes_asociaciones_schema():
    """
    Contrato: ND/NC deben poder quedar vinculadas a la FC que modifican.

    La tabla permite persistir la relacion comercial antes de resolver UI,
    service e integracion fiscal.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        columnas = db.execute(
            "PRAGMA table_info(ventas_comprobantes_asociaciones)"
        ).fetchall()
        indices = db.execute(
            "PRAGMA index_list(ventas_comprobantes_asociaciones)"
        ).fetchall()

    columnas_tabla = {columna["name"] for columna in columnas}
    indices_tabla = {indice["name"] for indice in indices}

    assert {
        "id",
        "comprobante_id",
        "comprobante_asociado_id",
        "tipo_relacion",
        "creado_en",
    }.issubset(columnas_tabla)
    assert "ux_ventas_comprobantes_asoc_comprobante" in indices_tabla
    assert "ux_ventas_comprobantes_asoc_par" in indices_tabla
    assert "ix_ventas_comprobantes_asoc_asociado" in indices_tabla


def test_ventas_comprobantes_asociaciones_permite_vincular_nd_a_fc():
    """
    Contrato estructural: una ND/NC puede apuntar al comprobante que modifica.

    La regla de negocio especifica de tipos se valida en service; la migracion
    solo crea integridad referencial entre comprobantes existentes.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        fc_id = _crear_comprobante_venta(db, cliente_id)

        cursor = db.execute(
            """
            INSERT INTO ventas_comprobantes (
                cliente_id,
                fecha,
                fecha_vencimiento,
                tipo_comprobante,
                tipo_comprobante_codigo,
                letra,
                punto_venta,
                numero,
                moneda_codigo,
                cotizacion_centavos,
                subtotal_centavos,
                descuento_centavos,
                recargo_centavos,
                iva_centavos,
                total_centavos,
                estado,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                "2026-01-16",
                "2026-02-16",
                "NOTA_DEBITO",
                "012",
                "C",
                1,
                1,
                "ARS",
                100,
                10000,
                0,
                0,
                0,
                10000,
                "BORRADOR",
                "2026-01-16 10:00:00",
            ),
        )
        nd_id = int(cursor.lastrowid)

        db.execute(
            """
            INSERT INTO ventas_comprobantes_asociaciones (
                comprobante_id,
                comprobante_asociado_id,
                tipo_relacion,
                creado_en
            )
            VALUES (?, ?, ?, ?)
            """,
            (nd_id, fc_id, "MODIFICA", "2026-01-16 10:05:00"),
        )

        asociacion = db.execute(
            """
            SELECT comprobante_id, comprobante_asociado_id, tipo_relacion
            FROM ventas_comprobantes_asociaciones
            WHERE comprobante_id = ?
            """,
            (nd_id,),
        ).fetchone()

    assert asociacion["comprobante_id"] == nd_id
    assert asociacion["comprobante_asociado_id"] == fc_id
    assert asociacion["tipo_relacion"] == "MODIFICA"


def test_ventas_comprobantes_asociaciones_rechaza_doble_asociacion_misma_nd():
    """
    Contrato inicial: cada ND/NC modifica una sola FC en esta etapa.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        cliente_id = _crear_cliente(db)

        fc_id = _crear_comprobante_venta(db, cliente_id)

        cursor = db.execute(
            """
            INSERT INTO ventas_comprobantes (
                cliente_id,
                fecha,
                tipo_comprobante,
                tipo_comprobante_codigo,
                letra,
                punto_venta,
                numero,
                moneda_codigo,
                cotizacion_centavos,
                subtotal_centavos,
                descuento_centavos,
                recargo_centavos,
                iva_centavos,
                total_centavos,
                estado,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                "2026-01-16",
                "NOTA_CREDITO",
                "013",
                "C",
                1,
                1,
                "ARS",
                100,
                10000,
                0,
                0,
                0,
                10000,
                "BORRADOR",
                "2026-01-16 10:00:00",
            ),
        )
        nc_id = int(cursor.lastrowid)

        db.execute(
            """
            INSERT INTO ventas_comprobantes_asociaciones (
                comprobante_id,
                comprobante_asociado_id,
                tipo_relacion,
                creado_en
            )
            VALUES (?, ?, ?, ?)
            """,
            (nc_id, fc_id, "MODIFICA", "2026-01-16 10:05:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO ventas_comprobantes_asociaciones (
                    comprobante_id,
                    comprobante_asociado_id,
                    tipo_relacion,
                    creado_en
                )
                VALUES (?, ?, ?, ?)
                """,
                (nc_id, fc_id, "MODIFICA", "2026-01-16 10:06:00"),
            )
