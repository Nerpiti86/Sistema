from app.contabilidad.libros_contables_service import obtener_contexto_mayor_general


def _saldos_mayor_general():
    return [
        {
            "cuenta_contable_codigo": "1.1.03.01.001",
            "cuenta_nombre": "Deudores por ventas",
            "cuenta_saldo_habitual": "DEBE",
            "cuenta_naturaleza": "PATRIMONIAL",
            "cuenta_imputable": 1,
            "cuenta_monetaria": 1,
            "saldo_inicial_debe_centavos": 1000000,
            "saldo_inicial_haber_centavos": 200000,
            "total_debe_periodo_centavos": 3500000,
            "total_haber_periodo_centavos": 500000,
        },
        {
            "cuenta_contable_codigo": "4.1.01.01.001",
            "cuenta_nombre": "Ingresos por servicios",
            "cuenta_saldo_habitual": "HABER",
            "cuenta_naturaleza": "RESULTADO",
            "cuenta_imputable": 1,
            "cuenta_monetaria": 0,
            "saldo_inicial_debe_centavos": 0,
            "saldo_inicial_haber_centavos": 1000000,
            "total_debe_periodo_centavos": 0,
            "total_haber_periodo_centavos": 3500000,
        },
    ]


def test_service_mayor_general_calcula_saldos_naturales(monkeypatch):
    """Valida saldos inicial, periodo y final por saldo habitual."""
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.listar_saldos_mayor_general",
        lambda ejercicio_id, fecha_desde, fecha_hasta, estado: (
            _saldos_mayor_general()
        ),
    )

    contexto = obtener_contexto_mayor_general(
        1,
        "2026-06-01",
        "2026-06-30",
    )

    assert contexto["cantidad_cuentas"] == 2
    assert contexto["total_debe_periodo_centavos"] == 3500000
    assert contexto["total_haber_periodo_centavos"] == 4000000
    assert contexto["diferencia_periodo_centavos"] == -500000
    assert contexto["diferencia_periodo_argentina"] == "-5.000,00"

    cuenta_debe = contexto["mayor_general_cuentas"][0]
    assert cuenta_debe["cuenta"] == "1.1.03.01.001"
    assert cuenta_debe["saldo_habitual"] == "DEBE"
    assert cuenta_debe["saldo_inicial_centavos"] == 800000
    assert cuenta_debe["saldo_periodo_centavos"] == 3000000
    assert cuenta_debe["saldo_final_centavos"] == 3800000
    assert cuenta_debe["saldo_final_argentina"] == "38.000,00"

    cuenta_haber = contexto["mayor_general_cuentas"][1]
    assert cuenta_haber["cuenta"] == "4.1.01.01.001"
    assert cuenta_haber["saldo_habitual"] == "HABER"
    assert cuenta_haber["saldo_inicial_centavos"] == 1000000
    assert cuenta_haber["saldo_periodo_centavos"] == 3500000
    assert cuenta_haber["saldo_final_centavos"] == 4500000
    assert cuenta_haber["saldo_final_argentina"] == "45.000,00"


def test_service_mayor_general_devuelve_contexto_vacio(monkeypatch):
    """Valida contexto consistente cuando no hay cuentas con saldos."""
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.listar_saldos_mayor_general",
        lambda ejercicio_id, fecha_desde, fecha_hasta, estado: [],
    )

    contexto = obtener_contexto_mayor_general(
        1,
        "2026-06-01",
        "2026-06-30",
    )

    assert contexto["mayor_general_cuentas"] == []
    assert contexto["cantidad_cuentas"] == 0
    assert contexto["total_debe_periodo_centavos"] == 0
    assert contexto["total_haber_periodo_centavos"] == 0
    assert contexto["diferencia_periodo_argentina"] == "0,00"
