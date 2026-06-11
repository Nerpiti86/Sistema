from pathlib import Path


TEMPLATE_NUEVO_ASIENTO = Path(
    "app/contabilidad/templates/contabilidad/asientos_contables_nuevo.html"
)
JS_NUEVO_ASIENTO = Path("app/static/js/asientos_contables_nuevo_lookup_cuentas.js")


def test_template_nuevo_asiento_expone_totales_visuales():
    """
    Valida contrato HTML de totales visuales del nuevo asiento.

    La pantalla debe exponer hooks estables para Total Debe, Total Haber y
    Diferencia sin mezclar reglas contables en el template.
    """
    contenido = TEMPLATE_NUEVO_ASIENTO.read_text(encoding="utf-8")

    assert 'id="as-totales"' in contenido
    assert 'data-role="asiento-totales"' in contenido
    assert 'id="as-total-debe"' in contenido
    assert 'data-role="asiento-total-debe"' in contenido
    assert 'id="as-total-haber"' in contenido
    assert 'data-role="asiento-total-haber"' in contenido
    assert 'id="as-diferencia"' in contenido
    assert 'data-role="asiento-diferencia"' in contenido


def test_js_nuevo_asiento_actualiza_totales_visuales():
    """
    Valida contrato JS de totales visuales del nuevo asiento.

    Los totales se calculan en frontend desde los importes visibles y se
    recalculan al escribir, agregar o quitar renglones.
    """
    contenido = JS_NUEVO_ASIENTO.read_text(encoding="utf-8")

    assert "ASIENTOS_SELECTOR_TOTAL_DEBE" in contenido
    assert "ASIENTOS_SELECTOR_TOTAL_HABER" in contenido
    assert "ASIENTOS_SELECTOR_DIFERENCIA" in contenido
    assert "ASIENTOS_SELECTOR_IMPORTE_CONTABLE" in contenido
    assert "normalizarImporteArgentinoACentavos" in contenido
    assert "formatearCentavosArgentino" in contenido
    assert "actualizarTotalesAsiento" in contenido
    assert "actualizarClaseDiferencia" in contenido
    assert "actualizarTotalesAsiento();" in contenido
