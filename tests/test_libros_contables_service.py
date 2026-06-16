from pathlib import Path

from app.contabilidad.libros_contables_service import obtener_contexto_libro_diario


def _movimientos_base():
    return [
        {
            "asiento_id": 10,
            "ejercicio_id": 1,
            "ejercicio_codigo": "2026",
            "numero_asiento": 7,
            "fecha": "2026-06-16",
            "asiento_descripcion": (
                "Comprobante: FC C 0001-00000001 | Sujeto: Nerpiti Nicolas Neri"
            ),
            "estado": "CONFIRMADO",
            "tipo": "VENTA",
            "detalle_id": 101,
            "renglon": 1,
            "cuenta_contable_codigo": "1.1.03.01.001",
            "cuenta_nombre": "Deudores por ventas",
            "detalle_descripcion": "Linea deudores",
            "debe_centavos": 3500000,
            "haber_centavos": 0,
        },
        {
            "asiento_id": 10,
            "ejercicio_id": 1,
            "ejercicio_codigo": "2026",
            "numero_asiento": 7,
            "fecha": "2026-06-16",
            "asiento_descripcion": (
                "Comprobante: FC C 0001-00000001 | Sujeto: Nerpiti Nicolas Neri"
            ),
            "estado": "CONFIRMADO",
            "tipo": "VENTA",
            "detalle_id": 102,
            "renglon": 2,
            "cuenta_contable_codigo": "4.1.01.01.001",
            "cuenta_nombre": "Ingresos por servicios",
            "detalle_descripcion": "Linea resultado",
            "debe_centavos": 0,
            "haber_centavos": 3500000,
        },
    ]


def test_libros_contables_service_no_usa_sql_directo():
    """
    Valida arquitectura del service de libros contables.

    El service puede agrupar, formatear y calcular totales, pero no debe acceder
    a la base ni ejecutar SQL.
    """
    contenido = Path("app/contabilidad/libros_contables_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido


def test_service_libro_diario_agrupa_asiento_y_calcula_totales(monkeypatch):
    """Valida agrupacion funcional del Libro Diario desde movimientos planos."""
    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.listar_movimientos_libro_diario",
        lambda ejercicio_id, fecha_desde, fecha_hasta, estado: _movimientos_base(),
    )

    contexto = obtener_contexto_libro_diario(
        1,
        "2026-06-01",
        "2026-06-30",
    )

    assert contexto["cantidad_asientos"] == 1
    assert contexto["total_debe_centavos"] == 3500000
    assert contexto["total_haber_centavos"] == 3500000
    assert contexto["diferencia_centavos"] == 0
    assert contexto["total_debe_argentina"] == "35.000,00"
    assert contexto["total_haber_argentina"] == "35.000,00"
    assert contexto["diferencia_argentina"] == "0,00"

    asiento = contexto["libro_diario_asientos"][0]
    assert asiento["numero_asiento"] == 7
    assert asiento["numero_asiento_mostrar"] == "EJ2026-0000007"
    assert asiento["fecha_argentina"] == "16/06/2026"
    assert asiento["comprobante"] == "FC C 0001-00000001"
    assert asiento["sujeto"] == "Nerpiti Nicolas Neri"
    assert asiento["total_debe_argentina"] == "35.000,00"
    assert asiento["total_haber_argentina"] == "35.000,00"
    assert asiento["diferencia_argentina"] == "0,00"
    assert len(asiento["renglones"]) == 2
    assert asiento["renglones"][0]["cuenta"] == "1.1.03.01.001"
    assert asiento["renglones"][0]["cuenta_nombre"] == "Deudores por ventas"
    assert asiento["renglones"][0]["debe_argentina"] == "35.000,00"
    assert asiento["renglones"][0]["haber_argentina"] == "0,00"


def test_service_libro_diario_tolera_descripcion_sin_comprobante(monkeypatch):
    """Valida fallback cuando el asiento no trae descripcion normalizada."""
    movimientos = _movimientos_base()
    movimientos[0]["asiento_descripcion"] = "Asiento manual sin origen"
    movimientos[1]["asiento_descripcion"] = "Asiento manual sin origen"

    monkeypatch.setattr(
        "app.contabilidad.libros_contables_service.listar_movimientos_libro_diario",
        lambda ejercicio_id, fecha_desde, fecha_hasta, estado: movimientos,
    )

    contexto = obtener_contexto_libro_diario(1)

    asiento = contexto["libro_diario_asientos"][0]
    assert asiento["comprobante"] == ""
    assert asiento["sujeto"] == ""
    assert asiento["descripcion"] == "Asiento manual sin origen"
