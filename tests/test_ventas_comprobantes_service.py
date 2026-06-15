import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.ventas_comprobantes_service import (
    confirmar_comprobante_venta,
    crear_borrador_comprobante_venta,
    crear_y_confirmar_comprobante_venta_desde_formulario,
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



def _crear_cuenta_deudores_ventas(db, cuenta="1.1.03.01.997") -> str:
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
            "Deudores por ventas test",
            "DEBE",
            "PATRIMONIAL",
            1,
            1,
            None,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def _asignar_cuenta_deudores_cliente(db, cliente_id: int, cuenta_codigo: str) -> None:
    db.execute(
        """
        UPDATE clientes
        SET cuenta_deudores_ventas_codigo = ?
        WHERE id = ?
        """,
        (cuenta_codigo, cliente_id),
    )


def _obtener_o_crear_ejercicio_venta(db) -> int:
    fila = db.execute(
        """
        SELECT id
        FROM ejercicios_contables
        WHERE fecha_desde <= ?
          AND fecha_hasta >= ?
        ORDER BY id
        LIMIT 1
        """,
        ("2026-01-15", "2026-01-15"),
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
            "Ejercicio test ventas",
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
        "iva_centavos": "0",
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
    assert comprobante["letra"] == "C"
    assert comprobante["moneda_codigo"] == "ARS"
    assert comprobante["subtotal_centavos"] == 100000
    assert comprobante["descuento_centavos"] == 0
    assert comprobante["recargo_centavos"] == 0
    assert comprobante["iva_centavos"] == 0
    assert comprobante["total_centavos"] == 100000
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
                }
            ],
        )

    detalle = comprobante["detalles"][0]
    assert detalle["descripcion"] == "Consulta inicial"
    assert detalle["precio_unitario_centavos"] == 150000
    assert detalle["subtotal_centavos"] == 150000
    assert detalle["iva_centavos"] == 0
    assert detalle["total_linea_centavos"] == 150000
    assert detalle["cuenta_ingreso_codigo"] == cuenta_ingreso
    assert comprobante["total_centavos"] == 150000


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
                }
            ],
        )

    assert comprobante["subtotal_centavos"] == 50000
    assert comprobante["iva_centavos"] == 0
    assert comprobante["total_centavos"] == 50000


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
                }
            ],
        )

    assert comprobante["subtotal_centavos"] == 100000
    assert comprobante["descuento_centavos"] == 15000
    assert comprobante["recargo_centavos"] == 2000
    assert comprobante["iva_centavos"] == 0
    assert comprobante["total_centavos"] == 87000


def test_crear_borrador_comprobante_venta_calcula_bonificacion_por_monto():
    """El service guarda tipo e importe de bonificacion por monto en el renglon."""
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
                    "tipo_bonificacion_codigo": "2",
                    "bonificacion_valor_10000": "15000",
                }
            ],
        )

    detalle = comprobante["detalles"][0]
    assert detalle["unidad_medida_codigo"] == "7"
    assert detalle["tipo_bonificacion_codigo"] == "2"
    assert detalle["bonificacion_valor_10000"] == 15000
    assert detalle["descuento_centavos"] == 15000
    assert detalle["subtotal_centavos"] == 100000
    assert detalle["total_linea_centavos"] == 85000
    assert comprobante["descuento_centavos"] == 15000
    assert comprobante["total_centavos"] == 85000


def test_crear_borrador_comprobante_venta_calcula_bonificacion_por_porcentaje():
    """El service calcula importe de bonificacion desde porcentaje informado."""
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
                    "unidad_medida_codigo": "14",
                    "tipo_bonificacion_codigo": "1",
                    "bonificacion_valor_10000": "100000",
                }
            ],
        )

    detalle = comprobante["detalles"][0]
    assert detalle["unidad_medida_codigo"] == "14"
    assert detalle["unidad_medida_descripcion"] == "gramos"
    assert detalle["tipo_bonificacion_codigo"] == "1"
    assert detalle["bonificacion_valor_10000"] == 100000
    assert detalle["descuento_centavos"] == 10000
    assert detalle["subtotal_centavos"] == 100000
    assert detalle["total_linea_centavos"] == 90000
    assert comprobante["descuento_centavos"] == 10000
    assert comprobante["total_centavos"] == 90000


def test_crear_borrador_comprobante_venta_rechaza_iva_hasta_contrato_fiscal():
    """El service bloquea IVA hasta definir condicion fiscal, alicuota y cuenta."""
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

        with pytest.raises(ValueError, match="IVA"):
            crear_borrador_comprobante_venta(
                _datos_comprobante(cliente_id),
                [
                    {
                        **_detalle(articulo_id),
                        "iva_centavos": "21000",
                    }
                ],
            )


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


def test_crear_y_confirmar_comprobante_venta_desde_formulario_genera_venta_asiento_y_ctacte():
    """
    Contrato: el usuario carga datos y al confirmar se genera todo el circuito.

    La operacion crea venta confirmada, asiento confirmado y movimiento de
    cuenta corriente confirmado. No debe quedar BORRADOR como resultado final.
    """
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _obtener_o_crear_ejercicio_venta(db)
        cuenta_deudores = _crear_cuenta_deudores_ventas(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.996",
            "Ingresos por servicios confirmacion directa",
        )
        cliente_id = _crear_cliente(db)
        _asignar_cuenta_deudores_cliente(db, cliente_id, cuenta_deudores)
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        resultado = crear_y_confirmar_comprobante_venta_desde_formulario(
            {
                **_datos_comprobante(cliente_id, numero=27),
                "articulo_venta_id": str(articulo_id),
                "cantidad": "1,00",
                "precio_unitario_centavos": "1.000,00",
                "unidad_medida_codigo": "7",
                "tipo_bonificacion_codigo": "",
                "bonificacion_valor": "0,00",
            }
        )

    comprobante = resultado["comprobante"]
    asiento = resultado["asiento"]
    movimiento = resultado["movimiento_cuenta_corriente"]

    assert comprobante["estado"] == "CONFIRMADO"
    assert comprobante["asiento_id"] == asiento["id"]
    assert asiento["estado"] == "CONFIRMADO"
    assert asiento["numero_asiento"] == 1
    assert movimiento["estado"] == "CONFIRMADO"
    assert movimiento["tipo_movimiento"] == "FACTURA"
    assert movimiento["origen_tipo"] == "VENTA_COMPROBANTE"
    assert movimiento["origen_id"] == comprobante["id"]
    assert movimiento["asiento_id"] == asiento["id"]


def test_confirmar_comprobante_venta_factura_genera_asiento_y_cuenta_corriente():
    """Confirma factura ARS sin IVA y genera impactos contables y de cuenta corriente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _obtener_o_crear_ejercicio_venta(db)
        cuenta_deudores = _crear_cuenta_deudores_ventas(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        cliente_id = _crear_cliente(db)
        _asignar_cuenta_deudores_cliente(db, cliente_id, cuenta_deudores)
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        comprobante = crear_borrador_comprobante_venta(
            _datos_comprobante(cliente_id),
            [_detalle(articulo_id)],
        )

        resultado = confirmar_comprobante_venta(comprobante["id"])

    comprobante_confirmado = resultado["comprobante"]
    asiento = resultado["asiento"]
    movimiento = resultado["movimiento_cuenta_corriente"]

    assert comprobante_confirmado["estado"] == "CONFIRMADO"
    assert comprobante_confirmado["asiento_id"] == asiento["id"]
    assert asiento["estado"] == "CONFIRMADO"
    assert asiento["tipo"] == "AJUSTE"
    assert movimiento["estado"] == "CONFIRMADO"
    assert movimiento["tipo_movimiento"] == "FACTURA"
    assert movimiento["debe_centavos"] == 100000
    assert movimiento["haber_centavos"] == 0
    assert movimiento["origen_tipo"] == "VENTA_COMPROBANTE"
    assert movimiento["origen_id"] == comprobante["id"]
    assert movimiento["asiento_id"] == asiento["id"]

    detalles_asiento = asiento["detalles"]
    assert detalles_asiento[0]["cuenta_contable_codigo"] == cuenta_deudores
    assert detalles_asiento[0]["debe_centavos"] == 100000
    assert detalles_asiento[0]["haber_centavos"] == 0
    assert detalles_asiento[1]["cuenta_contable_codigo"] == cuenta_ingreso
    assert detalles_asiento[1]["debe_centavos"] == 0
    assert detalles_asiento[1]["haber_centavos"] == 100000


def test_confirmar_comprobante_venta_nota_credito_invierte_asiento_y_ctacte():
    """Confirma nota de credito ARS sin IVA invirtiendo DEBE/HABER."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _obtener_o_crear_ejercicio_venta(db)
        cuenta_deudores = _crear_cuenta_deudores_ventas(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        cliente_id = _crear_cliente(db)
        _asignar_cuenta_deudores_cliente(db, cliente_id, cuenta_deudores)
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        comprobante = crear_borrador_comprobante_venta(
            {
                **_datos_comprobante(cliente_id),
                "tipo_comprobante": "NOTA_CREDITO",
            },
            [_detalle(articulo_id)],
        )

        resultado = confirmar_comprobante_venta(comprobante["id"])

    asiento = resultado["asiento"]
    movimiento = resultado["movimiento_cuenta_corriente"]
    detalles_asiento = asiento["detalles"]

    assert movimiento["tipo_movimiento"] == "NOTA_CREDITO"
    assert movimiento["debe_centavos"] == 0
    assert movimiento["haber_centavos"] == 100000
    assert detalles_asiento[0]["cuenta_contable_codigo"] == cuenta_deudores
    assert detalles_asiento[0]["debe_centavos"] == 0
    assert detalles_asiento[0]["haber_centavos"] == 100000
    assert detalles_asiento[1]["cuenta_contable_codigo"] == cuenta_ingreso
    assert detalles_asiento[1]["debe_centavos"] == 100000
    assert detalles_asiento[1]["haber_centavos"] == 0


def test_confirmar_comprobante_venta_rechaza_cliente_sin_cuenta_deudores():
    """La confirmacion exige cuenta deudores por ventas en el cliente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _obtener_o_crear_ejercicio_venta(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        cliente_id = _crear_cliente(db)
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        comprobante = crear_borrador_comprobante_venta(
            _datos_comprobante(cliente_id),
            [_detalle(articulo_id)],
        )

        with pytest.raises(ValueError, match="deudores"):
            confirmar_comprobante_venta(comprobante["id"])


def test_confirmar_comprobante_venta_rollback_si_falla_confirmacion_comercial(monkeypatch):
    """
    Contrato: confirmar venta es una operacion transaccional unica.

    Si falla despues de crear asiento y cuenta corriente, no debe quedar asiento,
    movimiento ni comprobante confirmado a medias.
    """
    import app.gestion.ventas_comprobantes_service as ventas_service

    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _obtener_o_crear_ejercicio_venta(db)
        cuenta_deudores = _crear_cuenta_deudores_ventas(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.996",
            "Ingresos por servicios rollback",
        )
        cliente_id = _crear_cliente(db)
        _asignar_cuenta_deudores_cliente(db, cliente_id, cuenta_deudores)
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        comprobante = crear_borrador_comprobante_venta(
            _datos_comprobante(cliente_id, numero=26),
            [_detalle(articulo_id)],
        )
        db.commit()

        def fallar_confirmacion_comercial(*_args, **_kwargs):
            raise ValueError("fallo controlado al confirmar venta")

        monkeypatch.setattr(
            ventas_service,
            "marcar_venta_comprobante_confirmado",
            fallar_confirmacion_comercial,
        )

        with pytest.raises(ValueError, match="fallo controlado"):
            ventas_service.confirmar_comprobante_venta(comprobante["id"])

        comprobante_actual = obtener_comprobante_venta(comprobante["id"])
        cantidad_asientos = db.execute(
            "SELECT COUNT(*) AS cantidad FROM asientos_contables"
        ).fetchone()["cantidad"]
        cantidad_movimientos = db.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM clientes_cuenta_corriente_movimientos
            WHERE origen_tipo = 'VENTA_COMPROBANTE'
              AND origen_id = ?
            """,
            (comprobante["id"],),
        ).fetchone()["cantidad"]

    assert comprobante_actual["estado"] == "BORRADOR"
    assert comprobante_actual["asiento_id"] is None
    assert cantidad_asientos == 0
    assert cantidad_movimientos == 0


def test_confirmar_comprobante_venta_rechaza_confirmar_dos_veces():
    """No permite confirmar nuevamente un comprobante ya confirmado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _obtener_o_crear_ejercicio_venta(db)
        cuenta_deudores = _crear_cuenta_deudores_ventas(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        cliente_id = _crear_cliente(db)
        _asignar_cuenta_deudores_cliente(db, cliente_id, cuenta_deudores)
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        comprobante = crear_borrador_comprobante_venta(
            _datos_comprobante(cliente_id),
            [_detalle(articulo_id)],
        )

        confirmar_comprobante_venta(comprobante["id"])

        with pytest.raises(ValueError, match="BORRADOR"):
            confirmar_comprobante_venta(comprobante["id"])


def test_confirmar_comprobante_venta_rechaza_moneda_no_ars():
    """La primera etapa de confirmacion solo confirma ventas ARS."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _obtener_o_crear_ejercicio_venta(db)
        cuenta_deudores = _crear_cuenta_deudores_ventas(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        cliente_id = _crear_cliente(db)
        _asignar_cuenta_deudores_cliente(db, cliente_id, cuenta_deudores)
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso, moneda_codigo="USD")

        comprobante = crear_borrador_comprobante_venta(
            {
                **_datos_comprobante(cliente_id),
                "moneda_codigo": "USD",
            },
            [_detalle(articulo_id)],
        )

        with pytest.raises(ValueError, match="ARS"):
            confirmar_comprobante_venta(comprobante["id"])


def test_confirmar_comprobante_venta_rechaza_descuento_global_no_asignable():
    """La confirmacion bloquea descuentos globales sin cuenta contable definida."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _obtener_o_crear_ejercicio_venta(db)
        cuenta_deudores = _crear_cuenta_deudores_ventas(db)
        cuenta_ingreso = _crear_cuenta_contable(
            db,
            "4.1.01.01.997",
            "Ingresos por servicios test",
        )
        cliente_id = _crear_cliente(db)
        _asignar_cuenta_deudores_cliente(db, cliente_id, cuenta_deudores)
        articulo_id = _crear_articulo_venta(db, cuenta_ingreso)

        comprobante = crear_borrador_comprobante_venta(
            {
                **_datos_comprobante(cliente_id),
                "descuento_centavos": "5000",
            },
            [_detalle(articulo_id)],
        )

        with pytest.raises(ValueError, match="descuento global"):
            confirmar_comprobante_venta(comprobante["id"])


def test_service_ventas_comprobantes_confirmacion_sigue_sin_sql_ni_get_db():
    """Contrato de capas: confirmacion en service sin SQL directo ni get_db."""
    from pathlib import Path

    contenido = Path("app/gestion/ventas_comprobantes_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert "SELECT " not in contenido
    assert "INSERT " not in contenido
    assert "UPDATE " not in contenido
    assert "DELETE " not in contenido

