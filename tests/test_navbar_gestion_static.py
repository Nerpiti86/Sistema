from pathlib import Path


def _bloque_gestion(html: str) -> str:
    posicion_gestion = html.index('id="ns-nav-gestion"')
    return html[posicion_gestion : html.index('id="ns-nav-contabilidad"', posicion_gestion)]


def test_navbar_gestion_usa_orden_aprobado():
    """
    Contrato de navegacion: Gestion expone Clientes y Ventas con el orden aprobado.

    Clientes:
    - Grupo clientes
    - Cliente

    Ventas:
    - Articulos
    - Nuevo comprobante
    - Comprobantes
    """
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")
    bloque_gestion = _bloque_gestion(html)

    assert 'class="dropdown-menu ns-dropdown-menu ns-mega-menu ns-mega-menu-wide"' in bloque_gestion

    assert 'id="ns-nav-clientes"' in bloque_gestion
    assert 'id="ns-nav-grupos-clientes"' in bloque_gestion
    assert 'id="ns-nav-clientes-maestro"' in bloque_gestion
    assert "Grupo clientes" in bloque_gestion
    assert "Cliente" in bloque_gestion
    assert "gestion.ver_listado_grupos_clientes" in bloque_gestion
    assert "gestion.ver_listado_clientes" in bloque_gestion

    assert 'id="ns-nav-ventas"' in bloque_gestion
    assert 'id="ns-nav-productos-servicios-venta"' in bloque_gestion
    assert 'id="ns-nav-nuevo-comprobante-venta"' in bloque_gestion
    assert 'id="ns-nav-comprobantes-venta"' in bloque_gestion
    assert "Artículos" in bloque_gestion
    assert "Nuevo comprobante" in bloque_gestion
    assert "Comprobantes" in bloque_gestion
    assert "gestion.ver_listado_productos_servicios_venta" in bloque_gestion
    assert "gestion.ver_formulario_nuevo_comprobante_venta" in bloque_gestion
    assert "gestion.ver_listado_comprobantes_venta" in bloque_gestion

    posiciones = [
        bloque_gestion.index('id="ns-nav-clientes"'),
        bloque_gestion.index('id="ns-nav-grupos-clientes"'),
        bloque_gestion.index('id="ns-nav-clientes-maestro"'),
        bloque_gestion.index('id="ns-nav-ventas"'),
        bloque_gestion.index('id="ns-nav-productos-servicios-venta"'),
        bloque_gestion.index('id="ns-nav-nuevo-comprobante-venta"'),
        bloque_gestion.index('id="ns-nav-comprobantes-venta"'),
    ]

    assert posiciones == sorted(posiciones)


def test_navbar_gestion_activa_nuevo_comprobante():
    """Contrato visual: la pantalla de nuevo comprobante debe activar Ventas."""
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")
    bloque_gestion = _bloque_gestion(html)

    assert "{% set es_nuevo_comprobante_venta = endpoint_actual in [" in html
    assert '"gestion.ver_formulario_nuevo_comprobante_venta"' in html
    assert '"gestion.crear_comprobante_venta_nuevo"' in html
    assert "{% set es_comprobantes_venta = es_nuevo_comprobante_venta or es_listado_comprobantes_venta %}" in html
    assert "{% if es_articulos_venta or es_comprobantes_venta %}active{% endif %}" in bloque_gestion


def test_navbar_gestion_no_menciona_productos_servicios_compra():
    """Valida que el menu no anticipe el circuito de compras."""
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")
    bloque_gestion = _bloque_gestion(html)

    assert "Productos o servicios para la compra" not in bloque_gestion
    assert "productos-servicios-compra" not in bloque_gestion
