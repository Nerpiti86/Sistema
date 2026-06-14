from pathlib import Path

from app import create_app
from app.contabilidad.ejercicios_contables_repository import crear_ejercicio_contable
from app.config import TestConfig
from app.db import apply_migrations, get_db


def _crear_ejercicio_contable_para_detalle():
    ejercicio_contable = crear_ejercicio_contable(
        {
            "codigo": "EJ2026",
            "nombre": "Ejercicio 2026",
            "fecha_desde": "2026-01-01",
            "fecha_hasta": "2026-12-31",
            "estado": "ABIERTO",
            "activo": True,
            "fase_cierre": "BLOQUEADO",
            "bloqueado": True,
            "bloqueado_en": "2026-01-02 10:11:12",
            "observaciones_cierre": "Detalle de prueba",
            "es_primer_ejercicio": True,
        }
    )

    db = get_db()
    db.execute(
        """
        UPDATE ejercicios_contables
        SET creado_en = ?,
            actualizado_en = ?
        WHERE codigo = ?
        """,
        ("2026-01-01 09:08:07", "2026-01-03 12:13:14", "EJ2026"),
    )
    db.commit()

    return ejercicio_contable


def test_listado_muestra_accion_detalle_de_ejercicio_contable():
    """
    Valida acceso desde listado al detalle de ejercicios_contables.

    La accion usa data-action y data-row-codigo para trazabilidad sin depender
    de texto visual exclusivamente.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_para_detalle()

        response = client.get("/contabilidad/ejercicios-contables/")

    assert response.status_code == 200
    assert b'data-field="acciones"' in response.data
    assert b'data-action="ver_detalle_ejercicio_contable"' in response.data
    assert b'data-row-codigo="EJ2026"' in response.data
    assert b"/contabilidad/ejercicios-contables/EJ2026/" in response.data
    assert b"Detalle" in response.data


def test_get_detalle_ejercicio_contable_muestra_datos_reales():
    """
    Valida pantalla de detalle de solo lectura.

    El detalle lee un ejercicio puntual por codigo via service y muestra campos
    reales de la tabla ejercicios_contables.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        _crear_ejercicio_contable_para_detalle()

        response = client.get("/contabilidad/ejercicios-contables/EJ2026/")

    assert response.status_code == 200
    assert b'id="ec-detalle"' in response.data
    assert b'data-query="obtener_contexto_detalle_ejercicio_contable"' in response.data
    assert b'data-row-codigo="EJ2026"' in response.data
    assert b"EJ2026" in response.data
    assert b"Ejercicio 2026" in response.data
    assert b"01/01/2026" in response.data
    assert b"31/12/2026" in response.data
    assert b"01/01/2026 09:08:07" in response.data
    assert b"02/01/2026 10:11:12" in response.data
    assert b"03/01/2026 12:13:14" in response.data
    assert b"2026-01-01" not in response.data
    assert b"2026-12-31" not in response.data
    assert b"2026-01-01 09:08:07" not in response.data
    assert b"2026-01-02 10:11:12" not in response.data
    assert b"2026-01-03 12:13:14" not in response.data
    assert b"ABIERTO" in response.data
    assert b"Detalle de prueba" in response.data
    assert b'data-field="es_primer_ejercicio"' in response.data


def test_detalle_ejercicio_contable_usa_resumen_visual_de_datos():
    """
    Contrato visual: el bloque de datos del ejercicio debe ser escaneable.

    La card principal separa identidad, estados, vigencia y metadatos sin
    volver al listado plano de definiciones.
    """
    html = Path(
        "app/contabilidad/templates/contabilidad/ejercicios_contables_detalle.html"
    ).read_text(encoding="utf-8")
    css = Path("app/static/css/nerisoft_theme.css").read_text(encoding="utf-8")

    assert "ns-detail-summary" in html
    assert "ns-detail-statuses" in html
    assert "ns-detail-period" in html
    assert "ns-detail-grid" in html
    assert "ns-detail-badge" in html
    assert 'data-field="codigo"' in html
    assert 'data-field="estado"' in html
    assert 'data-field="fecha_desde"' in html
    assert 'data-field="fecha_hasta"' in html
    assert 'data-field="observaciones_cierre"' in html

    assert ".ns-detail-summary" in css
    assert "background-color: var(--ns-color-main);" in css
    assert ".ns-detail-badge" in css
    assert "display: inline-flex;" in css
    assert "align-items: center;" in css
    assert ".ns-detail-grid" in css


def test_get_detalle_ejercicio_contable_inexistente_redirige_al_listado():
    """
    Valida manejo de inexistente en route detalle.

    Si el codigo no existe, la route no rompe y vuelve al listado con flash.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()

        response = client.get(
            "/contabilidad/ejercicios-contables/NOEXISTE/",
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/contabilidad/ejercicios-contables/"
    )
