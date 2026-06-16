from pathlib import Path


def _bloque_contabilidad(html: str) -> str:
    posicion_contabilidad = html.index('id="ns-nav-contabilidad"')
    return html[
        posicion_contabilidad : html.index('id="ns-nav-tablas-comunes"', posicion_contabilidad)
    ]


def test_navbar_contabilidad_usa_orden_aprobado_por_grupos():
    """
    Contrato de navegacion: Contabilidad expone Ejercicios, Cuentas, Asientos y Libros
    en el orden aprobado.
    """
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")
    bloque_contabilidad = _bloque_contabilidad(html)

    assert 'id="ns-nav-ejercicios"' in bloque_contabilidad
    assert 'id="ns-nav-ejercicio"' in bloque_contabilidad
    assert 'id="ns-nav-indices"' in bloque_contabilidad

    assert 'id="ns-nav-cuentas"' in bloque_contabilidad
    assert 'id="ns-nav-listado-cuentas-contables"' in bloque_contabilidad
    assert 'id="ns-nav-cuentas-contables"' in bloque_contabilidad

    assert 'id="ns-nav-asientos"' in bloque_contabilidad
    assert 'id="ns-nav-nuevo-asiento"' in bloque_contabilidad
    assert 'id="ns-nav-listado-asientos"' in bloque_contabilidad

    assert 'id="ns-nav-libros"' in bloque_contabilidad
    assert 'id="ns-nav-libro-diario"' in bloque_contabilidad
    assert 'id="ns-nav-libro-mayor"' in bloque_contabilidad
    assert 'id="ns-nav-libro-mayor-general"' in bloque_contabilidad

    posiciones = [
        bloque_contabilidad.index('id="ns-nav-ejercicios"'),
        bloque_contabilidad.index('id="ns-nav-ejercicio"'),
        bloque_contabilidad.index('id="ns-nav-indices"'),
        bloque_contabilidad.index('id="ns-nav-cuentas"'),
        bloque_contabilidad.index('id="ns-nav-listado-cuentas-contables"'),
        bloque_contabilidad.index('id="ns-nav-cuentas-contables"'),
        bloque_contabilidad.index('id="ns-nav-asientos"'),
        bloque_contabilidad.index('id="ns-nav-nuevo-asiento"'),
        bloque_contabilidad.index('id="ns-nav-listado-asientos"'),
        bloque_contabilidad.index('id="ns-nav-libros"'),
    ]

    assert posiciones == sorted(posiciones)


def test_navbar_asientos_marca_activo_el_grupo_del_mega_menu():
    """
    Contrato visual: cualquier pantalla de asientos debe activar el grupo Asientos
    dentro del mega menu Contabilidad.
    """
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")

    assert "{% set es_asientos = endpoint_actual in [" in html
    assert '"contabilidad.ver_formulario_nuevo_asiento_contable"' in html
    assert '"contabilidad.crear_asiento_contable_nuevo"' in html
    assert '"contabilidad.ver_listado_asientos_contables"' in html
    assert '"contabilidad.ver_detalle_asiento_contable"' in html
    assert (
        'id="ns-nav-asientos" class="ns-mega-section-title {% if es_asientos %}active{% endif %}"'
        in html
    )
