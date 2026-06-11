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
    assert "ASIENTOS_SELECTOR_CANTIDAD_RENGLONES" in contenido
    assert "actualizarCantidadRenglonesAsiento" in contenido
    assert "textContent = String(obtenerRenglonesAsiento().length)" in contenido


def test_js_renglones_dinamicos_limpia_select_moneda_al_clonar():
    """
    Valida que el clonado contemple selects de moneda por renglon.

    Al agregar un renglon nuevo, la moneda debe volver a ARS para no heredar
    accidentalmente la moneda nominal del renglon anterior.
    """
    with open(
        "app/static/js/asientos_contables_nuevo_lookup_cuentas.js",
        encoding="utf-8",
    ) as archivo_js:
        contenido = archivo_js.read()

    assert 'querySelectorAll("input, select")' in contenido
    assert 'campo === "moneda_codigo"' in contenido
    assert 'campoRenglon.value = "ARS";' in contenido


def test_template_renglon_moneda_expone_badge_ciclico_y_conserva_select_post():
    """
    Valida contrato HTML para moneda por renglon como badge.

    El select real conserva el name del POST y el badge visible solo actua como
    control de UI para ciclar la moneda sin tocar backend.
    """
    with open(
        "app/contabilidad/templates/contabilidad/asientos_contables_nuevo.html",
        encoding="utf-8",
    ) as archivo_template:
        contenido = archivo_template.read()

    assert 'data-role="asiento-moneda-renglon"' in contenido
    assert 'name="detalles[{{ renglon_idx }}][moneda_codigo]"' in contenido
    assert 'class="visually-hidden"' in contenido
    assert 'tabindex="-1"' in contenido
    assert 'data-role="asiento-moneda-badge"' in contenido
    assert 'data-action="ciclar-moneda-renglon"' in contenido
    assert 'type="button"' in contenido
    assert "ns-moneda-badge" in contenido


def test_js_renglon_moneda_badge_cicla_select_y_dispara_change():
    """
    Valida contrato JS del badge de moneda.

    El badge debe ciclar sobre las opciones reales del select, sincronizar su
    texto visible y disparar change para reutilizar el recalculo FX existente.
    """
    with open(
        "app/static/js/asientos_contables_nuevo_lookup_cuentas.js",
        encoding="utf-8",
    ) as archivo_js:
        contenido = archivo_js.read()

    assert "ASIENTOS_SELECTOR_MONEDA_BADGE" in contenido
    assert "function obtenerBadgeMonedaRenglon" in contenido
    assert "function sincronizarBadgeMonedaRenglon" in contenido
    assert "function ciclarMonedaRenglon" in contenido
    assert "inputMoneda.options.length" in contenido
    assert "inputMoneda.selectedIndex" in contenido
    assert "(indiceActual + 1) % cantidadOpciones" in contenido
    assert 'dispatchEvent(new Event("change", { bubbles: true }))' in contenido
    assert "sincronizarBadgeMonedaRenglon(renglonAsiento);" in contenido
