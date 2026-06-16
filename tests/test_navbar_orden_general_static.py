from pathlib import Path


def test_navbar_orden_principal_aprobado():
    """Contrato de navegacion principal: Inicio, Gestion, Contabilidad, Tablas comunes."""
    html = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")

    ids_ordenados = [
        'id="ns-nav-inicio"',
        'id="ns-nav-gestion"',
        'id="ns-nav-contabilidad"',
        'id="ns-nav-tablas-comunes"',
    ]

    posiciones = [html.index(id_menu) for id_menu in ids_ordenados]

    assert posiciones == sorted(posiciones)
    assert "Inicio" in html
    assert "Gestión" in html
    assert "Contabilidad" in html
    assert "Tablas comunes" in html
