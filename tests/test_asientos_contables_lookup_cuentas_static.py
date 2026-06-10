def test_js_lookup_cuentas_imputables_asiento_tiene_contrato_identificable():
    """
    Valida JS aislado para lookup de cuentas imputables en nuevo asiento.

    El script debe usar data-hooks especificos y completar el nombre de cuenta
    sin mezclar la logica con otros formularios contables.
    """
    with open(
        "app/static/js/asientos_contables_nuevo_lookup_cuentas.js",
        encoding="utf-8",
    ) as archivo_js:
        contenido = archivo_js.read()

    assert "ASIENTOS_SELECTOR_LOOKUP_CUENTAS" in contenido
    assert "asientos-cuentas-imputables" in contenido
    assert "buscarCuentasImputablesParaAsiento" in contenido
    assert "renderizarOpcionesLookupCuenta" in contenido
    assert "aplicarCuentaSeleccionada" in contenido
    assert "inicializarLookupCuentasImputablesAsiento" in contenido
    assert "DOMContentLoaded" in contenido
    assert "fetch(" in contenido
    assert "obtenerRenglonesAsiento" in contenido
    assert "agregarRenglonAsiento" in contenido
    assert "quitarRenglonAsiento" in contenido
    assert "reindexarRenglonesAsiento" in contenido
