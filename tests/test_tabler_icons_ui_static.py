from pathlib import Path


def leer(ruta):
    return Path(ruta).read_text(encoding="utf-8")


def test_base_carga_tabler_icons_desde_cdn():
    contenido = leer("app/ui/templates/base.html")

    assert "@tabler/icons-webfont@latest/tabler-icons.min.css" in contenido
    assert "cdn.jsdelivr.net" in contenido


def test_datepicker_global_crea_boton_con_icono_tabler_calendar():
    js = leer("app/static/js/fecha_argentina_datepicker.js")
    css = leer("app/static/css/fecha_argentina_datepicker.css")

    assert "ns-date-field__button" in js
    assert "const crearIcono = (nombreIcono)" in js
    assert "icono.className = `ti ti-${nombreIcono}`" in js
    assert "appendChild(crearIcono(\"calendar\"))" in js
    assert "botonIcono" in js
    assert "estado.botonIcono.addEventListener" in js
    assert ".ns-date-field__button" in css
    assert "padding-right: 2.65rem" in css
    assert "innerHTML" not in js
    assert ".style" not in js
    assert "setAttribute(\"style\"" not in js


def test_navbar_reemplaza_flecha_bootstrap_por_ti_chevron_down():
    layout = leer("app/ui/templates/components/layout.html")
    css = leer("app/static/css/nerisoft_navbar.css")

    assert layout.count("ti ti-chevron-down ns-dropdown-chevron") == 3
    assert "ns-nav-tablas-comunes" in layout
    assert "ns-nav-gestion" in layout
    assert "ns-nav-contabilidad" in layout
    assert ".ns-navbar .dropdown-toggle::after" in css
    assert "display: none" in css
    assert ".ns-navbar .ns-dropdown-chevron" in css
    assert "transform: rotate(180deg)" in css


def test_select_custom_reemplaza_caracter_flecha_por_icono_tabler():
    js = leer("app/static/js/nerisoft_select.js")
    css = leer("app/static/css/nerisoft_select.css")

    assert "ti ti-chevron-down" in js
    assert "arrowIcon.setAttribute(\"aria-hidden\", \"true\")" in js
    assert "arrow.appendChild(arrowIcon)" in js
    assert "\"▼\"" not in js
    assert ".ns-select__arrow" in css
    assert "display: inline-flex" in css
