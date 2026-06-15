from pathlib import Path


def test_navbar_tablas_comunes_usa_mega_menu_por_grupos():
    """
    Contrato de navegación: Tablas comunes replica el patrón del mega menú
    ancho de Contabilidad, con módulo a la izquierda y grupos funcionales.
    """
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")

    posicion_tablas = html.index('id="ns-nav-tablas-comunes"')
    bloque_tablas = html[
        posicion_tablas : html.index('id="ns-nav-gestion"', posicion_tablas)
    ]

    assert 'class="dropdown-menu ns-dropdown-menu ns-mega-menu ns-mega-menu-wide"' in bloque_tablas
    assert 'id="ns-nav-tablas-operacion"' in bloque_tablas
    assert 'id="ns-nav-tablas-geografia"' in bloque_tablas
    assert 'id="ns-nav-tablas-fiscal"' in bloque_tablas

    assert "Monedas" in bloque_tablas
    assert "Bancos" in bloque_tablas
    assert "Medios operativos" in bloque_tablas
    assert "Países" in bloque_tablas
    assert "Provincias" in bloque_tablas
    assert "Condiciones IVA" in bloque_tablas
    assert "Tipos de documento" in bloque_tablas
    assert "Unidades de medida" in bloque_tablas
    assert "Tipos de bonificación" in bloque_tablas
    assert "Tipos de comprobantes" in bloque_tablas

    assert "{% if es_monedas or es_bancos or es_medios_operativos %}active{% endif %}" in bloque_tablas
    assert "{% if es_paises or es_provincias %}active{% endif %}" in bloque_tablas
    assert (
        "{% if es_condiciones_iva or es_tipos_documento or es_unidades_medida "
        "or es_tipos_bonificacion or es_tipos_comprobante %}active{% endif %}"
    ) in bloque_tablas

    posicion_operacion = bloque_tablas.index('id="ns-nav-tablas-operacion"')
    posicion_monedas = bloque_tablas.index('id="ns-nav-monedas"')
    posicion_bancos = bloque_tablas.index('id="ns-nav-bancos"')
    posicion_medios = bloque_tablas.index('id="ns-nav-medios-operativos"')
    posicion_geografia = bloque_tablas.index('id="ns-nav-tablas-geografia"')
    posicion_paises = bloque_tablas.index('id="ns-nav-paises"')
    posicion_provincias = bloque_tablas.index('id="ns-nav-provincias"')
    posicion_fiscal = bloque_tablas.index('id="ns-nav-tablas-fiscal"')
    posicion_iva = bloque_tablas.index('id="ns-nav-condiciones-iva"')
    posicion_documento = bloque_tablas.index('id="ns-nav-tipos-documento"')
    posicion_unidades = bloque_tablas.index('id="ns-nav-unidades-medida"')
    posicion_bonificacion = bloque_tablas.index('id="ns-nav-tipos-bonificacion"')
    posicion_comprobante = bloque_tablas.index('id="ns-nav-tipos-comprobante"')

    assert (
        posicion_operacion
        < posicion_monedas
        < posicion_bancos
        < posicion_medios
        < posicion_geografia
        < posicion_paises
        < posicion_provincias
        < posicion_fiscal
        < posicion_iva
        < posicion_documento
        < posicion_unidades
        < posicion_bonificacion
        < posicion_comprobante
    )
