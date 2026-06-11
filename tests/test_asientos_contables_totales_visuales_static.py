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
    assert "ASIENTOS_SELECTOR_IMPORTE_NOMINAL" in contenido
    assert "ASIENTOS_SELECTOR_INPUT_DEBE_ARS" in contenido
    assert "ASIENTOS_SELECTOR_INPUT_HABER_ARS" in contenido
    assert "actualizarImportesArsRenglon" in contenido
    assert "actualizarImportesArsRenglones" in contenido
    assert "normalizarImporteArgentinoACentavos" in contenido
    assert "formatearCentavosArgentino" in contenido
    assert "actualizarTotalesAsiento" in contenido
    assert "actualizarClaseDiferencia" in contenido
    assert "actualizarTotalesAsiento();" in contenido


def test_template_nuevo_asiento_expone_boton_guardar_borrador_real():
    """
    Valida contrato HTML del boton real de guardado del nuevo asiento.

    El bloqueo visual debe apoyarse en hooks existentes sin renombrar la accion
    del POST ni cambiar el contrato del formulario.
    """
    contenido = TEMPLATE_NUEVO_ASIENTO.read_text(encoding="utf-8")

    assert 'id="as-guardar"' in contenido
    assert 'data-action="crear_asiento_contable_borrador"' in contenido
    assert 'type="submit"' in contenido
    assert "Guardar borrador" in contenido


def test_js_nuevo_asiento_bloquea_guardar_borrador_si_no_balancea():
    """
    Valida contrato JS del bloqueo visual de guardado.

    El boton Guardar borrador debe deshabilitarse cuando la diferencia calculada
    en frontend sea distinta de cero, manteniendo el backend como control final.
    """
    contenido = JS_NUEVO_ASIENTO.read_text(encoding="utf-8")

    assert "ASIENTOS_SELECTOR_GUARDAR_BORRADOR" in contenido
    assert "#as-guardar" in contenido
    assert "ASIENTOS_MENSAJE_ASIENTO_DESBALANCEADO" in contenido
    assert "function actualizarEstadoBotonGuardarBorrador" in contenido
    assert "botonGuardarBorrador.disabled = debeBloquearGuardar;" in contenido
    assert "actualizarEstadoBotonGuardarBorrador(diferenciaCentavos);" in contenido


def test_template_nuevo_asiento_totales_indican_ars():
    """
    Valida que los totales visibles sean explicitamente contables en ARS.

    Los importes nominales son la entrada del usuario, pero la diferencia y el
    bloqueo de guardado deben apoyarse visualmente en los importes ARS.
    """
    contenido = TEMPLATE_NUEVO_ASIENTO.read_text(encoding="utf-8")

    assert "Total Debe ARS" in contenido
    assert "Total Haber ARS" in contenido
    assert "Debe nominal" in contenido
    assert "Haber nominal" in contenido
    assert "Debe ARS" in contenido
    assert "Haber ARS" in contenido


def test_js_nuevo_asiento_fx_no_muestra_ars_falso():
    """
    Valida contrato visual transitorio para renglones FX.

    Mientras no exista preview AJAX de cotizacion, la UI no debe copiar nominal
    extranjero como si fuera ARS; debe indicar que se calcula al guardar.
    """
    contenido = JS_NUEVO_ASIENTO.read_text(encoding="utf-8")

    assert "ASIENTOS_SELECTOR_MONEDA_RENGLON" in contenido
    assert "ASIENTOS_MONEDA_CONTABLE" in contenido
    assert "ASIENTOS_TEXTO_CALCULO_AL_GUARDAR" in contenido
    assert "existeRenglonMonedaExtranjera" in contenido
    assert "obtenerMonedaRenglonAsiento" in contenido
    assert "Al guardar" in contenido
