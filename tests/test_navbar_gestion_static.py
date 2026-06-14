from pathlib import Path


def test_navbar_gestion_usa_mega_menu_por_grupos():
    """
    Contrato de navegación: Gestión usa el mismo patrón de mega menú ancho,
    con módulo a la izquierda y accesos agrupados a la derecha. El grupo
    Clientes contiene maestro de clientes y grupos de clientes.
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

    assert "{% if es_grupos_clientes or es_clientes %}active{% endif %}" in bloque_gestion

    posicion_clientes = bloque_gestion.index('id="ns-nav-clientes"')
    posicion_maestro = bloque_gestion.index('id="ns-nav-clientes-maestro"')
    posicion_grupos = bloque_gestion.index('id="ns-nav-grupos-clientes"')

    assert (
        posicion_clientes
        < posicion_maestro
        < posicion_grupos
    )
