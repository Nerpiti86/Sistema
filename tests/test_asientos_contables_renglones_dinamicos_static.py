from pathlib import Path

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


def test_moneda_badge_tiene_formato_visual_por_moneda():
    """
    Valida contrato visual del badge de moneda por renglon.

    ARS, USD y EUR deben tener colores propios y usar Roboto Mono importada
    desde Google Fonts, sin cambiar el contrato POST del select real.
    """
    with open("app/ui/templates/base.html", encoding="utf-8") as archivo_base:
        base = archivo_base.read()

    with open(
        "app/static/css/nerisoft_typography.css",
        encoding="utf-8",
    ) as archivo_tipografia:
        tipografia = archivo_tipografia.read()

    with open(
        "app/static/css/nerisoft_theme.css",
        encoding="utf-8",
    ) as archivo_theme:
        theme = archivo_theme.read()

    with open(
        "app/contabilidad/templates/contabilidad/asientos_contables_nuevo.html",
        encoding="utf-8",
    ) as archivo_template:
        template = archivo_template.read()

    with open(
        "app/static/js/asientos_contables_nuevo_lookup_cuentas.js",
        encoding="utf-8",
    ) as archivo_js:
        js = archivo_js.read()

    assert "Roboto+Mono:wght@500;600;700&display=swap" in base
    assert '--ns-font-family-mono: "Roboto Mono";' in tipografia

    assert "font-family: var(--ns-font-family-mono);" in theme
    assert ".ns-moneda-badge--ars" in theme
    assert "#e0f2fe" in theme
    assert "#0284c7" in theme
    assert ".ns-moneda-badge--usd" in theme
    assert "#dcfce7" in theme
    assert "#16a34a" in theme
    assert ".ns-moneda-badge--eur" in theme
    assert "#f3e8ff" in theme
    assert "#9333ea" in theme

    assert "ASIENTOS_MONEDA_BADGE_CLASES" in js
    assert "function obtenerClaseBadgeMoneda" in js
    assert "classList.add(obtenerClaseBadgeMoneda(monedaRenglon))" in js
    assert (
        'class="btn btn-sm badge rounded-pill text-bg-light border '
        'border-secondary ns-moneda-badge px-2 py-1"'
        not in template
    )
    assert "ns-moneda-badge--{{ detalle_asiento.moneda_codigo|lower }}" in template


def test_js_campos_cotizacion_y_nominales_borran_al_hacer_focus():
    """
    Contrato UX: cotizacion, debe nominal y haber nominal se limpian al foco.

    El borrado se delega desde el contenedor de renglones para cubrir renglones
    dinamicos, respeta readonly/disabled y dispara eventos para recalcular.
    """
    contenido = Path(
        "app/static/js/asientos_contables_nuevo_lookup_cuentas.js"
    ).read_text(encoding="utf-8")

    assert "ASIENTOS_SELECTOR_INPUT_BORRAR_FOCUS_RENGLON" in contenido
    assert "ASIENTOS_SELECTOR_IMPORTE_NOMINAL" in contenido
    assert "function manejarFocusinInputBorrableRenglon" in contenido
    assert '"focusin"' in contenido
    assert "manejarFocusinInputBorrableRenglon" in contenido
    assert "inputRenglon.readOnly" in contenido
    assert "inputRenglon.disabled" in contenido
    assert 'inputRenglon.value = "";' in contenido
    assert 'dispatchEvent(new Event("input", { bubbles: true }))' in contenido
    assert 'dispatchEvent(new Event("change", { bubbles: true }))' in contenido
    assert 'input[data-field="nominal_debe_centavos"]' in contenido
    assert 'input[data-field="nominal_haber_centavos"]' in contenido
    assert 'input[data-field="cotizacion_1000000"]' in contenido
