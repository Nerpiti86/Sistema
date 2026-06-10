from pathlib import Path


def test_base_carga_tema_visual_global():
    """
    Valida que el contrato visual global se cargue desde base.html.

    El tema debe ser global para evitar estilos repetidos por pantalla.
    """
    contenido = Path("app/ui/templates/base.html").read_text(encoding="utf-8")

    assert "css/nerisoft_theme.css" in contenido


def test_tema_visual_global_declara_paleta_y_tablas():
    """
    Valida contrato de paleta y tablas.

    Las tablas deben tener borde exterior oscuro, encabezado oscuro,
    acento amarillo y filas sin alternancia visual.
    """
    contenido = Path("app/static/css/nerisoft_theme.css").read_text(encoding="utf-8")

    assert "--ns-color-accent: #FFD966;" in contenido
    assert "--ns-color-main: #262626;" in contenido
    assert "--ns-color-soft: #F2F2F2;" in contenido
    assert "--ns-table-card-padding: 15px;" in contenido
    assert ".ns-card .table thead th" in contenido
    assert "border-bottom: 3px solid var(--ns-color-accent);" in contenido
    assert ".ns-card .table-striped > tbody > tr:nth-of-type(odd) > *" in contenido


def test_tema_visual_global_declara_botones():
    """
    Valida contrato de botones globales.

    btn-primary debe usar negro principal y los secundarios deben usar acento
    amarillo con fondo transparente.
    """
    contenido = Path("app/static/css/nerisoft_theme.css").read_text(encoding="utf-8")

    assert ".btn-primary" in contenido
    assert "--bs-btn-bg: var(--ns-color-main);" in contenido
    assert ".btn-secondary" in contenido
    assert ".btn-outline-primary" in contenido
    assert "--bs-btn-border-color: var(--ns-color-accent);" in contenido


def test_card_component_expone_clases_globales():
    """
    Valida que el componente card quede marcado para tema global.

    Esto permite aplicar formato consistente sin modificar cada pantalla.
    """
    contenido = Path("app/ui/templates/components/cards.html").read_text(
        encoding="utf-8"
    )

    assert 'class="card ns-card"' in contenido
    assert 'class="card-body ns-card-body"' in contenido


def test_no_quedan_table_striped_en_templates():
    """
    Valida que no queden tablas alternadas por Bootstrap.

    El contrato visual indica filas sin alternancia.
    """
    rutas_con_striped = []

    for ruta in Path("app").rglob("*.html"):
        contenido = ruta.read_text(encoding="utf-8")
        if "table-striped" in contenido:
            rutas_con_striped.append(str(ruta))

    assert rutas_con_striped == []
