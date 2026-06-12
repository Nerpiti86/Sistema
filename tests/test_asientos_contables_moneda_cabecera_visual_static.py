from pathlib import Path


TEMPLATE_DIR = Path("app/contabilidad/templates/contabilidad")


def _leer_template(nombre_archivo: str) -> str:
    return (TEMPLATE_DIR / nombre_archivo).read_text(encoding="utf-8")


def test_listado_asientos_nombra_moneda_de_cabecera_como_cabecera_contable():
    """Valida que el listado no presente la moneda de cabecera como moneda operativa del asiento."""

    contenido = _leer_template("asientos_contables.html")

    assert '<th data-field="moneda_origen_codigo">Cabecera contable</th>' in contenido
    assert '<th data-field="cotizacion_1000000" class="text-end">Cotiz. cabecera</th>' in contenido
    assert '<th data-field="moneda_origen_codigo">Moneda</th>' not in contenido
    assert '<th data-field="cotizacion_1000000" class="text-end">Cotización</th>' not in contenido


def test_detalle_asiento_aclara_que_moneda_real_vive_en_renglones():
    """Valida que el detalle distinga cabecera contable de moneda real por renglón."""

    contenido = _leer_template("asientos_contables_detalle.html")

    assert '<dt class="col-sm-3">Cabecera contable</dt>' in contenido
    assert '<dt class="col-sm-3">Cotiz. cabecera</dt>' in contenido
    assert 'id="as-detalle-renglones-ayuda"' in contenido
    assert 'data-role="ayuda-renglones-moneda"' in contenido
    assert "La moneda real y la cotización se leen por renglón" in contenido
    assert '<dt class="col-sm-3">Monedas</dt>' not in contenido
