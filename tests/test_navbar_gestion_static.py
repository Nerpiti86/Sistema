from pathlib import Path


def test_navbar_gestion_usa_mega_menu_por_grupos():
    """
    Contrato de navegación: Gestión usa el mismo patrón de mega menú ancho,
    con módulo a la izquierda y accesos agrupados a la derecha.

    El grupo Clientes contiene maestro de clientes y grupos de clientes.
    El grupo Ventas contiene productos/servicios y comprobantes de venta.
    """
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")

    posicion_gestion = html.index('id="ns-nav-gestion"')
    bloque_gestion = html[
        posicion_gestion : html.index('id="ns-nav-contabilidad"', posicion_gestion)
    ]

    assert 'class="dropdown-menu ns-dropdown-menu ns-mega-menu ns-mega-menu-wide"' in bloque_gestion

    assert 'id="ns-nav-clientes"' in bloque_gestion
    assert 'id="ns-nav-segmentacion-clientes"' not in bloque_gestion
    assert 'id="ns-nav-clientes-maestro"' in bloque_gestion
    assert 'id="ns-nav-grupos-clientes"' in bloque_gestion

    assert 'id="ns-nav-ventas"' in bloque_gestion
    assert 'id="ns-nav-productos-servicios-venta"' in bloque_gestion
    assert "Productos o servicios para la venta" in bloque_gestion
    assert "gestion.ver_listado_productos_servicios_venta" in bloque_gestion
    assert 'id="ns-nav-comprobantes-venta"' in bloque_gestion
    assert "Comprobantes de venta" in bloque_gestion
    assert "gestion.ver_listado_comprobantes_venta" in bloque_gestion

    assert "{% if es_grupos_clientes or es_clientes %}active{% endif %}" in bloque_gestion
    assert "{% if es_productos_servicios_venta or es_comprobantes_venta %}active{% endif %}" in bloque_gestion
    assert "{% if es_productos_servicios_venta %}active{% endif %}" in bloque_gestion
    assert "{% if es_comprobantes_venta %}active{% endif %}" in bloque_gestion

    posicion_clientes = bloque_gestion.index('id="ns-nav-clientes"')
    posicion_maestro = bloque_gestion.index('id="ns-nav-clientes-maestro"')
    posicion_grupos = bloque_gestion.index('id="ns-nav-grupos-clientes"')
    posicion_ventas = bloque_gestion.index('id="ns-nav-ventas"')
    posicion_productos_servicios_venta = bloque_gestion.index(
        'id="ns-nav-productos-servicios-venta"'
    )
    posicion_comprobantes_venta = bloque_gestion.index(
        'id="ns-nav-comprobantes-venta"'
    )

    assert (
        posicion_clientes
        < posicion_maestro
        < posicion_grupos
        < posicion_ventas
        < posicion_productos_servicios_venta
        < posicion_comprobantes_venta
    )


def test_navbar_gestion_no_menciona_productos_servicios_compra():
    """Valida que el acceso nuevo no anticipe el circuito de compras."""
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")
    posicion_gestion = html.index('id="ns-nav-gestion"')
    bloque_gestion = html[
        posicion_gestion : html.index('id="ns-nav-contabilidad"', posicion_gestion)
    ]

    assert "Productos o servicios para la compra" not in bloque_gestion
    assert "productos-servicios-compra" not in bloque_gestion
