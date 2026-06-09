from pathlib import Path

from app import create_app
from app.config import TestConfig


def test_base_carga_google_fonts_inter_y_css_global_de_tipografia():
    """
    Valida contrato global de fuente.

    El layout base debe importar Inter desde Google Fonts y luego cargar la hoja
    propia de NeriSoft para centralizar fuente y numeros tabulares.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "https://fonts.googleapis.com" in html
    assert "https://fonts.gstatic.com" in html
    assert "family=Inter:wght@400;500;600;700&display=swap" in html
    assert "css/nerisoft_typography.css" in html
    assert html.index("fonts.googleapis.com") < html.index("css/nerisoft_typography.css")


def test_css_global_define_inter_sin_fallbacks_y_tabular_nums():
    """
    Valida contrato CSS global.

    La fuente declarada es Inter sin fallbacks. Los numeros usan tabular-nums
    para estabilizar columnas, importes y codigos contables.
    """
    css_path = Path("app/static/css/nerisoft_typography.css")

    assert css_path.exists()

    css = css_path.read_text(encoding="utf-8")

    assert '--ns-font-sans: "Inter";' in css
    assert '--ns-font-numeric: "Inter";' in css
    assert "system-ui" not in css
    assert "-apple-system" not in css
    assert "BlinkMacSystemFont" not in css
    assert "Segoe UI" not in css
    assert "Roboto" not in css
    assert "Arial" not in css
    assert "sans-serif" not in css
    assert "font-variant-numeric: tabular-nums;" in css
    assert '"tnum" 1' in css
    assert '"lnum" 1' in css
    assert "[data-field]" in css
    assert "[data-row-codigo]" in css
    assert ".ns-tabular-num" in css
