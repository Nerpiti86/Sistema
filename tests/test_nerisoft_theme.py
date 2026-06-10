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


def test_tema_visual_global_declara_fondo_y_sombra_de_cards():
    """
    Valida fondo general y sombra de cards.

    El fondo de la app debe ser gris claro, y los cards deben usar borde
    apenas mas oscuro y sombra difusa pareja desde todos los bordes.
    """
    contenido = Path("app/static/css/nerisoft_theme.css").read_text(encoding="utf-8")

    assert "body {" in contenido
    assert "background-color: var(--ns-color-soft);" in contenido
    assert "--ns-color-card-border: #D0D0D0;" in contenido
    assert "--ns-shadow-card: 0 0 1.15rem rgba(38, 38, 38, 0.10);" in contenido
    assert "box-shadow: var(--ns-shadow-card);" in contenido


def test_datepicker_respeta_contrato_visual_global():
    """
    Valida que el datepicker use paleta y sombra global.

    No debe depender del primary de Bootstrap para estados seleccionados.
    """
    contenido = Path("app/static/css/fecha_argentina_datepicker.css").read_text(
        encoding="utf-8"
    )

    assert "border: 1px solid var(--ns-color-card-border);" in contenido
    assert "background: var(--ns-color-card-bg);" in contenido
    assert "box-shadow: var(--ns-shadow-floating);" in contenido
    assert "background: var(--ns-color-main);" in contenido
    assert "outline: 2px solid var(--ns-color-accent);" in contenido
    assert "var(--bs-primary)" not in contenido


def test_select_respeta_contrato_visual_global():
    """
    Valida que el select custom use paleta y sombra global.

    El control, panel, busqueda y opciones deben quedar alineados al tema.
    """
    contenido = Path("app/static/css/nerisoft_select.css").read_text(
        encoding="utf-8"
    )

    assert "border: 1px solid var(--ns-color-card-border);" in contenido
    assert "background: var(--ns-color-card-bg);" in contenido
    assert "box-shadow: var(--ns-shadow-floating);" in contenido
    assert "border-color: var(--ns-color-accent);" in contenido
    assert "background: var(--ns-color-main);" in contenido
    assert "var(--bs-primary)" not in contenido


def test_tema_visual_global_refina_tablas():
    """
    Valida refinamiento visual de tablas.

    El encabezado debe medir al menos 35px, el borde debe ser de 2px,
    la fuente del encabezado debe quedar normal y la tabla debe tener padding.
    """
    contenido = Path("app/static/css/nerisoft_theme.css").read_text(encoding="utf-8")

    assert "--ns-table-border-width: 2px;" in contenido
    assert "--ns-table-header-height: 35px;" in contenido
    assert "--ns-table-outer-padding: 8px;" in contenido
    assert "border: var(--ns-table-border-width) solid var(--ns-color-main);" in contenido
    assert "min-height: var(--ns-table-header-height);" in contenido
    assert "height: var(--ns-table-header-height);" in contenido
    assert "font-weight: 400;" in contenido
    assert "padding: var(--ns-table-cell-padding-y) var(--ns-table-cell-padding-x);" in contenido


def test_navbar_respeta_contrato_visual_global():
    """
    Valida que navbar use el contrato visual global.

    El navbar no debe depender del fondo tertiary de Bootstrap y debe usar
    negro principal, texto claro, acento amarillo y dropdowns tematizados.
    """
    layout = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")
    css = Path("app/static/css/nerisoft_navbar.css").read_text(encoding="utf-8")

    assert "bg-body-tertiary" not in layout
    assert "background-color: var(--ns-color-main) !important;" in css
    assert "border-bottom: 2px solid var(--ns-color-accent) !important;" in css
    assert "color: var(--ns-color-soft) !important;" in css
    assert "box-shadow: var(--ns-shadow-floating);" in css
    assert ".ns-navbar .dropdown-item.active" in css


def test_tema_visual_global_refina_tablas_con_encabezado_contenido():
    """
    Valida que el encabezado de tabla quede contenido.

    El borde exterior debe quedar en 2px, el encabezado debe medir 35px,
    la fuente debe ser normal y debe existir padding externo para que el
    encabezado no llegue pegado al borde.
    """
    contenido = Path("app/static/css/nerisoft_theme.css").read_text(encoding="utf-8")

    assert "--ns-table-border-width: 2px;" in contenido
    assert "--ns-table-header-height: 35px;" in contenido
    assert "--ns-table-outer-padding: 8px;" in contenido
    assert "border: var(--ns-table-border-width) solid var(--ns-color-main);" in contenido
    assert "border: 0;" in contenido
    assert "min-height: var(--ns-table-header-height);" in contenido
    assert "height: var(--ns-table-header-height);" in contenido
    assert "font-weight: 400;" in contenido
    assert "padding: var(--ns-table-cell-padding-y) var(--ns-table-cell-padding-x);" in contenido


def test_navbar_respeta_contrato_visual_global():
    """
    Valida que navbar use el contrato visual global.

    El navbar no debe depender del fondo tertiary de Bootstrap y debe usar
    negro principal, texto claro, acento amarillo y dropdowns tematizados.
    """
    layout = Path("app/ui/templates/components/layout.html").read_text(encoding="utf-8")
    css = Path("app/static/css/nerisoft_navbar.css").read_text(encoding="utf-8")

    assert "bg-body-tertiary" not in layout
    assert "background-color: var(--ns-color-main) !important;" in css
    assert "border-bottom: 2px solid var(--ns-color-accent) !important;" in css
    assert "color: var(--ns-color-soft) !important;" in css
    assert "box-shadow: var(--ns-shadow-floating);" in css
    assert ".ns-navbar .dropdown-item.active" in css


def test_navbar_dropdown_padres_internos_tienen_contraste():
    """
    Valida contraste de dropdowns padre internos.

    Los toggles principales del navbar deben ser claros sobre fondo oscuro,
    pero los dropdowns padre internos, como Cuentas y Ejercicios, deben ser
    oscuros porque viven dentro de un menu claro.
    """
    css = Path("app/static/css/nerisoft_navbar.css").read_text(encoding="utf-8")

    assert ".ns-navbar .dropdown-menu .dropdown-toggle" in css
    assert "color: var(--ns-color-main) !important;" in css
    assert ".dropdown-submenu.show > .dropdown-toggle" in css
    assert "color: var(--ns-color-white) !important;" in css
    assert ".ns-navbar .navbar-brand," in css
    assert ".navbar-nav > .nav-item > .nav-link" in css
