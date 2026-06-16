from app.contabilidad.libros_contables_service import obtener_contexto_mayor_por_cuenta


def _cuenta_debe():
    return {
        "cuenta": "1.1.03.01.001",
        "descripcion": "Deudores por ventas",
        "saldo_habitual": "DEBE",
        "naturaleza": "PATRIMONIAL",
        "imputable": 1,
        "monetaria": 1,
    }


def _cuenta_haber():
    return {
        "cuenta": "4.1.01.01.001",
        "descripcion": "Ingresos por servicios",
        "saldo_habitual": "HABER",
        "naturaleza": "RESULTADO",
        "imputable": 1,
        "monetaria": 0,
    }


def _movimientos_cuenta_debe():
    return [
        {
            "asiento_id": 10,
            "ejercicio_id": 1,
            "ejercicio_codigo": "2026",
            "numero_asiento": 7,
            "fecha": "2026-06-16",
            "asiento_descripcion": (
                "Comprobante: FC C 0001-00000001 | Sujeto: Cliente mayor"
            ),
            "estado": "CONFIRMADO",
            "tipo": "VENTA",
            "detalle_id": 101,
            "renglon": 1,
            "cuenta_contable_codigo": "1.1.03.01.001",
            "cuenta_nombre": "Deudores por ventas",
            "detalle_descripcion": "Factura cliente",
            "debe_centavos": 3500000,
            "haber_centavos": 0,
        },
        {
            "asiento_id": 11,
            "ejercicio_id": 1,
            "ejercicio_codigo": "2026",
            "numero_asiento": 8,
            "fecha": "2026-06-20",
            "asiento_descripcion": (
                "Comprobante: NC C 0001-00000001 | Sujeto: Cliente mayor"
            ),
            "estado": "CONFIRMADO",
            "tipo": "VENTA",
            "detalle_id": 102,
            "renglon": 1,
            "cuenta_contable_codigo": "1.1.03.01.001",
            "cuenta_nombre": "Deudores por ventas",
            "detalle_descripcion": "Nota credito cliente",
            "debe_centavos": 0,
            "haber_centavos": 500000,
        },
    ]


def test_service_mayor_por_cuenta_debe_calcula_saldos_acumulados(monkeypatch):
    """Valida mayor de una cuenta de saldo habitual DEBE."""
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.obtener_cuenta_contable_por_cuenta",
        lambda cuenta: _cuenta_debe(),
    )
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.obtener_saldo_inicial_mayor_por_cuenta",
        lambda ejercicio_id, cuenta, fecha_desde, estado: {
            "debe_centavos": 1000000,
            "haber_centavos": 200000,
        },
    )
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.listar_movimientos_mayor_por_cuenta",
        lambda ejercicio_id, cuenta, fecha_desde, fecha_hasta, estado: (
            _movimientos_cuenta_debe()
        ),
    )

    contexto = obtener_contexto_mayor_por_cuenta(
        1,
        "1.1.03.01.001",
        "2026-06-01",
        "2026-06-30",
    )

    assert contexto["cuenta_contable"]["cuenta"] == "1.1.03.01.001"
    assert contexto["cuenta_contable"]["saldo_habitual"] == "DEBE"
    assert contexto["saldo_inicial_centavos"] == 800000
    assert contexto["saldo_inicial_argentina"] == "8.000,00"
    assert contexto["total_debe_periodo_centavos"] == 3500000
    assert contexto["total_haber_periodo_centavos"] == 500000
    assert contexto["saldo_periodo_centavos"] == 3000000
    assert contexto["saldo_final_centavos"] == 3800000
    assert contexto["saldo_final_argentina"] == "38.000,00"

    movimientos = contexto["mayor_movimientos"]
    assert len(movimientos) == 2
    assert movimientos[0]["numero_asiento_mostrar"] == "EJ2026-0000007"
    assert movimientos[0]["fecha_argentina"] == "16/06/2026"
    assert movimientos[0]["comprobante"] == "FC C 0001-00000001"
    assert movimientos[0]["sujeto"] == "Cliente mayor"
    assert movimientos[0]["saldo_acumulado_centavos"] == 4300000
    assert movimientos[0]["saldo_acumulado_argentina"] == "43.000,00"
    assert movimientos[1]["saldo_acumulado_centavos"] == 3800000


def test_service_mayor_por_cuenta_haber_interpreta_saldo_natural(monkeypatch):
    """Valida que una cuenta HABER acumule haber menos debe."""
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.obtener_cuenta_contable_por_cuenta",
        lambda cuenta: _cuenta_haber(),
    )
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.obtener_saldo_inicial_mayor_por_cuenta",
        lambda ejercicio_id, cuenta, fecha_desde, estado: {
            "debe_centavos": 0,
            "haber_centavos": 1000000,
        },
    )
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.listar_movimientos_mayor_por_cuenta",
        lambda ejercicio_id, cuenta, fecha_desde, fecha_hasta, estado: [
            {
                **_movimientos_cuenta_debe()[0],
                "cuenta_contable_codigo": "4.1.01.01.001",
                "cuenta_nombre": "Ingresos por servicios",
                "debe_centavos": 0,
                "haber_centavos": 3500000,
            }
        ],
    )

    contexto = obtener_contexto_mayor_por_cuenta(
        1,
        "4.1.01.01.001",
        "2026-06-01",
        "2026-06-30",
    )

    assert contexto["cuenta_contable"]["saldo_habitual"] == "HABER"
    assert contexto["saldo_inicial_centavos"] == 1000000
    assert contexto["saldo_periodo_centavos"] == 3500000
    assert contexto["saldo_final_centavos"] == 4500000
    assert contexto["saldo_final_argentina"] == "45.000,00"
    assert contexto["mayor_movimientos"][0]["saldo_acumulado_argentina"] == "45.000,00"


def test_service_mayor_por_cuenta_rechaza_cuenta_inexistente(monkeypatch):
    """Valida mensaje claro cuando la cuenta no existe."""
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.obtener_cuenta_contable_por_cuenta",
        lambda cuenta: None,
    )

    try:
        obtener_contexto_mayor_por_cuenta(
            1,
            "1.1.03.01.001",
            "2026-06-01",
            "2026-06-30",
        )
    except ValueError as exc:
        error = str(exc)
    else:
        error = ""

    assert error == "No existe la cuenta contable seleccionada."
