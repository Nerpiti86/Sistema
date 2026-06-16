from pathlib import Path


def test_navbar_tablas_comunes_usa_mega_menu_por_grupos():
    """
    Contrato de navegacion: Tablas comunes queda al final del navbar y mantiene
    agrupacion por Operacion, Fiscal y Geografia.
    """
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")

    posicion_tablas = html.index('id="ns-nav-tablas-comunes"')
    bloque_tablas = html[posicion_tablas : html.index("</ul>", posicion_tablas)]

    assert 'class="dropdown-menu ns-dropdown-menu ns-mega-menu ns-mega-menu-wide"' in bloque_tablas
    assert 'id="ns-nav-tablas-operacion"' in bloque_tablas
    assert 'id="ns-nav-tablas-fiscal"' in bloque_tablas
    assert 'id="ns-nav-tablas-geografia"' in bloque_tablas

    assert "Monedas" in bloque_tablas
    assert "Bancos" in bloque_tablas
    assert "Medios operativos" in bloque_tablas
    assert "Tipos de comprobantes" in bloque_tablas
    assert "Condiciones IVA" in bloque_tablas
    assert "Tipos de documento" in bloque_tablas
    assert "Unidades de medida" in bloque_tablas
    assert "Tipos de bonificación" in bloque_tablas
    assert "Países" in bloque_tablas
    assert "Provincias" in bloque_tablas

    assert "{% if es_monedas or es_bancos or es_medios_operativos %}active{% endif %}" in bloque_tablas
    assert (
        "{% if es_tipos_comprobante or es_condiciones_iva or es_tipos_documento "
        "or es_unidades_medida or es_tipos_bonificacion %}active{% endif %}"
    ) in bloque_tablas
    assert "{% if es_paises or es_provincias %}active{% endif %}" in bloque_tablas

    posiciones = [
        bloque_tablas.index('id="ns-nav-tablas-operacion"'),
        bloque_tablas.index('id="ns-nav-monedas"'),
        bloque_tablas.index('id="ns-nav-bancos"'),
        bloque_tablas.index('id="ns-nav-medios-operativos"'),
        bloque_tablas.index('id="ns-nav-tablas-fiscal"'),
        bloque_tablas.index('id="ns-nav-tipos-comprobante"'),
        bloque_tablas.index('id="ns-nav-condiciones-iva"'),
        bloque_tablas.index('id="ns-nav-tipos-documento"'),
        bloque_tablas.index('id="ns-nav-unidades-medida"'),
        bloque_tablas.index('id="ns-nav-tipos-bonificacion"'),
        bloque_tablas.index('id="ns-nav-tablas-geografia"'),
        bloque_tablas.index('id="ns-nav-paises"'),
        bloque_tablas.index('id="ns-nav-provincias"'),
    ]

    assert posiciones == sorted(posiciones)
