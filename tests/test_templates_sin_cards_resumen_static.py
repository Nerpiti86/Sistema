from pathlib import Path
import re


PATRON_CARD_RESUMEN = re.compile(r"""{%\s*call\s+card\(\s*["']Resumen["']""")


def test_templates_no_usan_cards_resumen():
    """Contrato UI: no deben existir cards visuales tituladas Resumen en templates."""
    templates = sorted(Path("app").glob("**/templates/**/*.html"))

    ofensores = [
        str(path)
        for path in templates
        if PATRON_CARD_RESUMEN.search(path.read_text(encoding="utf-8"))
    ]

    assert ofensores == []
