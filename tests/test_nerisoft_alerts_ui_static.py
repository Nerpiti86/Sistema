from pathlib import Path


def leer(ruta):
    return Path(ruta).read_text(encoding="utf-8")


def test_alert_template_usa_icono_tabler_por_categoria():
    contenido = leer("app/ui/templates/components/alerts.html")

    assert "ns-alert-modal--{{ alert_category }}" in contenido
    assert "ns-alert-content" in contenido
    assert "ns-alert-icon" in contenido
    assert "ti ti-{{ alert_icon }}" in contenido
    assert "circle-check" in contenido
    assert "alert-triangle" in contenido
    assert "alert-circle" in contenido
    assert "info-circle" in contenido
    assert "shadow-lg" not in contenido
    assert "position-absolute top-0 end-0 m-3" not in contenido


def test_alert_css_define_disenio_blanco_sin_redondeo_con_linea_superior():
    contenido = leer("app/static/css/nerisoft_alerts.css")

    assert "background: #fff;" in contenido
    assert "border-radius: 0;" in contenido
    assert "box-shadow: 0 0.55rem 1.35rem" in contenido
    assert ".ns-alert-modal::before" in contenido
    assert "height: 0.42rem" in contenido
    assert ".ns-alert-modal--success" in contenido
    assert ".ns-alert-modal--danger" in contenido
    assert ".ns-alert-modal--warning" in contenido
    assert ".ns-alert-modal--info" in contenido
    assert ".ns-alert-icon" in contenido
    assert "border-radius: 1rem" not in contenido
    assert "border-radius: 0.875rem" not in contenido


def test_alert_css_define_tamanio_visible_y_sombra_no_bootstrap():
    contenido = leer("app/static/css/nerisoft_alerts.css")

    assert "width: min(48rem, calc(100% - 2rem));" in contenido
    assert "min-height: 5rem;" in contenido
    assert "font-size: 1rem;" in contenido
    assert "font-size: 1.55rem;" in contenido
