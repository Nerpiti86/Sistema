def test_js_renglones_dinamicos_nuevo_asiento_tiene_contrato_identificable():
    """
    Valida JS de agregar/quitar renglones del asiento.

    La logica debe clonar, limpiar y reindexar renglones sin tocar routes,
    service ni repository.
    """
    with open(
        "app/static/js/asientos_contables_nuevo_lookup_cuentas.js",
        encoding="utf-8",
    ) as archivo_js:
        contenido = archivo_js.read()

    assert "ASIENTOS_SELECTOR_RENGLONES" in contenido
    assert "ASIENTOS_SELECTOR_RENGLON" in contenido
    assert "ASIENTOS_SELECTOR_AGREGAR_RENGLON" in contenido
    assert "ASIENTOS_SELECTOR_QUITAR_RENGLON" in contenido
    assert "ASIENTOS_MINIMO_RENGLONES = 2" in contenido
    assert "cloneNode(true)" in contenido
    assert "limpiarRenglonClonado" in contenido
    assert "reemplazarIndiceRenglon" in contenido
    assert "detalles\\[\\d+\\]" in contenido
    assert "actualizarEstadoBotonesQuitarRenglon" in contenido
