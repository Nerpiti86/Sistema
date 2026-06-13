from pathlib import Path


def test_navbar_contabilidad_expone_grupo_asientos_en_mega_menu():
    """
    Contrato de navegación: el mega menú de Contabilidad expone accesos
    directos a nuevo asiento y listado de asientos sin depender de rutas ni SQL.
    """
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")

    assert "{% set es_asientos = endpoint_actual in [" in html
    assert '"contabilidad.ver_listado_asientos_contables"' in html
    assert '"contabilidad.ver_formulario_nuevo_asiento_contable"' in html
    assert '"contabilidad.crear_asiento_contable_nuevo"' in html
    assert '"contabilidad.ver_detalle_asiento_contable"' in html

    assert 'id="ns-nav-contabilidad"' in html
    assert 'class="dropdown-menu ns-dropdown-menu ns-mega-menu ns-mega-menu-wide"' in html
    assert 'id="ns-nav-asientos"' in html
    assert 'id="ns-nav-nuevo-asiento"' in html
    assert 'id="ns-nav-listado-asientos"' in html

    assert "Asientos" in html
    assert "Nuevo asiento" in html
    assert "Listado de asientos" in html

    assert 'data-module="asientos"' in html
    assert 'data-endpoint="contabilidad.ver_formulario_nuevo_asiento_contable"' in html
    assert 'data-endpoint="contabilidad.ver_listado_asientos_contables"' in html

    posicion_contabilidad = html.index('id="ns-nav-contabilidad"')
    posicion_asientos = html.index('id="ns-nav-asientos"')
    posicion_nuevo = html.index('id="ns-nav-nuevo-asiento"')
    posicion_listado = html.index('id="ns-nav-listado-asientos"')
    posicion_cuentas = html.index('id="ns-nav-cuentas"')

    assert (
        posicion_contabilidad
        < posicion_asientos
        < posicion_nuevo
        < posicion_listado
        < posicion_cuentas
    )


def test_navbar_asientos_marca_activo_el_grupo_del_mega_menu():
    """
    Contrato visual: cualquier pantalla de asientos debe activar el grupo
    Asientos dentro del mega menú Contabilidad.
    """
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")

    assert (
        'id="ns-nav-asientos" class="ns-mega-section-title {% if es_asientos %}active{% endif %}"'
        in html
    )

    assert "'contabilidad.ver_formulario_nuevo_asiento_contable'" in html
    assert "'contabilidad.crear_asiento_contable_nuevo'" in html
    assert "'contabilidad.ver_listado_asientos_contables'" in html
    assert "'contabilidad.ver_detalle_asiento_contable'" in html
