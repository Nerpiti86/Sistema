from pathlib import Path


def test_navbar_contabilidad_expone_libros_contables():
    """Contrato de navegacion: Contabilidad expone Libro diario, Libro mayor y Libro mayor general."""
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")
    posicion_contabilidad = html.index('id="ns-nav-contabilidad"')
    bloque_contabilidad = html[
        posicion_contabilidad : html.index('id="ns-nav-tablas-comunes"', posicion_contabilidad)
    ]

    assert "{% set es_libros = endpoint_actual in [" in html
    assert '"contabilidad.ver_libro_diario"' in html
    assert '"contabilidad.ver_mayor_por_cuenta"' in html
    assert '"contabilidad.ver_mayor_general"' in html

    assert 'id="ns-nav-libros"' in bloque_contabilidad
    assert 'id="ns-nav-libro-diario"' in bloque_contabilidad
    assert 'id="ns-nav-libro-mayor"' in bloque_contabilidad
    assert 'id="ns-nav-libro-mayor-general"' in bloque_contabilidad

    assert "Libro diario" in bloque_contabilidad
    assert "Libro mayor" in bloque_contabilidad
    assert "Libro mayor general" in bloque_contabilidad

    assert "url_for('contabilidad.ver_libro_diario')" in bloque_contabilidad
    assert "url_for('contabilidad.ver_mayor_por_cuenta')" in bloque_contabilidad
    assert "url_for('contabilidad.ver_mayor_general')" in bloque_contabilidad

    posiciones = [
        bloque_contabilidad.index('id="ns-nav-libros"'),
        bloque_contabilidad.index('id="ns-nav-libro-diario"'),
        bloque_contabilidad.index('id="ns-nav-libro-mayor"'),
        bloque_contabilidad.index('id="ns-nav-libro-mayor-general"'),
    ]

    assert posiciones == sorted(posiciones)
