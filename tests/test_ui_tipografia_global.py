from pathlib import Path

from app import create_app
from app.config import TestConfig


def test_base_carga_google_fonts_inter_y_css_global_de_tipografia():
    """
    Valida contrato global de fuente.

    El layout base debe importar Inter desde Google Fonts y luego cargar la hoja
    propia de NeriSoft para centralizar fuente, tamanios y numeros tabulares.
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

    assert '--ns-font-family-base: "Inter";' in css
    assert '--ns-font-family-numeric: "Inter";' in css
    assert "--ns-font-sans: var(--ns-font-family-base);" in css
    assert "--ns-font-numeric: var(--ns-font-family-numeric);" in css
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


def test_css_global_declara_contrato_de_tamanios_tipograficos():
    """
    Valida contrato de tamanios tipograficos NeriSoft.

    """
    css = Path("app/static/css/nerisoft_typography.css").read_text(
        encoding="utf-8"
    )

    assert "--ns-font-size-micro: 0.7rem;" in css
    assert "--ns-font-size-secondary: 0.8rem;" in css
    assert "--ns-font-size-table-dense: 0.8rem;" in css
    assert "--ns-font-size-form-dense: 0.8rem;" in css
    assert "--ns-font-size-base: 0.9rem;" in css
    assert "--ns-font-size-form: 0.9rem;" in css
    assert "--ns-font-size-title-section: 1.1rem;" in css
    assert "--ns-font-size-title-page: 1.5rem;" in css

    assert "font-size: var(--ns-font-size-base);" in css
    assert "font-size: var(--ns-font-size-form);" in css
    assert "font-size: var(--ns-font-size-form-dense);" in css
    assert "font-size: var(--ns-font-size-table-dense);" in css
    assert "font-size: var(--ns-font-size-title-page);" in css
    assert "font-size: var(--ns-font-size-title-section);" in css
    assert "font-size: var(--ns-font-size-secondary);" in css
    assert "font-size: var(--ns-font-size-micro);" in css


def test_css_global_declara_pesos_tipograficos():
    """Valida tokens de peso tipografico para evitar valores sueltos."""
    css = Path("app/static/css/nerisoft_typography.css").read_text(
        encoding="utf-8"
    )

    assert "--ns-font-weight-normal: 400;" in css
    assert "--ns-font-weight-medium: 500;" in css
    assert "--ns-font-weight-semibold: 600;" in css
    assert "--ns-font-weight-bold: 700;" in css
    assert "font-weight: var(--ns-font-weight-normal);" in css
    assert "font-weight: var(--ns-font-weight-semibold);" in css


def test_css_global_declara_contrato_numerico():
    """
    Valida contrato numerico.

    Importes y numeros usan Inter, alineacion derecha y numeros tabulares.
    """
    css = Path("app/static/css/nerisoft_typography.css").read_text(
        encoding="utf-8"
    )

    assert ".ns-numero," in css
    assert ".ns-importe" in css
    assert ".ns-codigo" in css
    assert "font-family: var(--ns-font-family-numeric);" in css
    assert "text-align: right;" in css
    assert ".text-end" in css
    assert ".table td" in css
    assert ".table th" in css
