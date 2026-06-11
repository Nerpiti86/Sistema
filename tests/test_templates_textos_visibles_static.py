from pathlib import Path
import re


def test_templates_no_renderizan_subtitulos_tecnicos_con_guion_bajo():
    """
    Contrato visual: los subtitulos visibles de cards no deben mostrar nombres
    tecnicos de tablas o entidades con guiones bajos.
    """
    templates = Path("app").glob("**/templates/**/*.html")
    patron = re.compile(
        r"card\(\s*['\"][^'\"]+['\"]\s*,\s*['\"][^'\"]*_[^'\"]*['\"]"
    )

    ocurrencias = []

    for template in templates:
        contenido = template.read_text(encoding="utf-8")
        if patron.search(contenido):
            ocurrencias.append(str(template))

    assert ocurrencias == []


def test_templates_no_conservan_textos_visibles_sin_tilde_relevantes():
    """
    Contrato visual: evita regresiones de textos visibles frecuentes sin tilde.
    No valida nombres tecnicos en minuscula usados por hooks HTML.
    """
    controles = {
        "app/ui/templates/dashboard.html": [
            "Base minima",
            "Flask modular - SQLite - Bootstrap original - Jinja macros",
        ],
        "app/ui/templates/errors/404.html": [
            "Pagina no encontrada.",
        ],
        "app/ui/templates/components/layout.html": [
            "Abrir navegacion",
        ],
        "app/contabilidad/templates/contabilidad/index.html": [
            "Modulo base registrado",
            "Base del modulo contable creada correctamente.",
        ],
        "app/contabilidad/templates/contabilidad/asientos_contables.html": [
            "La carga se habilitara en un paso posterior.",
            ">Observacion<",
            ">Numero<",
            ">Descripcion<",
            ">Cotizacion<",
        ],
        "app/contabilidad/templates/contabilidad/asientos_contables_nuevo.html": [
            ">Descripcion<",
            "Cotizacion por defecto",
            ">Cotizacion<",
            ">Accion<",
            "segun sea necesario",
        ],
        "app/contabilidad/templates/contabilidad/asientos_contables_detalle.html": [
            ">Numero<",
            ">Descripcion<",
            ">Cotizacion<",
            ">Renglon<",
        ],
        "app/contabilidad/templates/contabilidad/ejercicios_contables.html": [
            ">Codigo<",
            ">Si<",
        ],
        "app/contabilidad/templates/contabilidad/ejercicios_contables_form.html": [
            "Alta de registro en ejercicios_contables.",
            ">Codigo<",
        ],
        "app/contabilidad/templates/contabilidad/ejercicios_contables_detalle.html": [
            ">Codigo<",
            ">Si<",
            ">Periodo<",
            ">Indice inicio<",
            ">Periodo cierre<",
            ">Indice cierre<",
            "Coeficientes de inflacion",
        ],
        "app/tablas_comunes/templates/tablas_comunes/monedas.html": [
            "para gestion, contabilidad",
            ">Codigo<",
            ">Simbolo<",
            ">Si<",
        ],
    }

    hallazgos = []

    for ruta_relativa, textos_prohibidos in controles.items():
        contenido = Path(ruta_relativa).read_text(encoding="utf-8")
        for texto in textos_prohibidos:
            if texto in contenido:
                hallazgos.append(f"{ruta_relativa}: {texto}")

    assert hallazgos == []
