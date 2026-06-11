from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations


def test_base_carga_asset_global_numero_argentino():
    """
    Contrato: la conversion de punto a coma decimal vive en asset global.

    Los templates solo declaran data-decimal="argentino" y no usan JS inline.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/indices-inflacion/")

    assert response.status_code == 200
    assert b"js/numero_argentino.js" in response.data
    assert b"<script>" not in response.data


def test_input_indice_inflacion_declara_decimal_argentino():
    """
    Contrato: los inputs decimales argentinos declaran hook estable.

    El input sigue siendo el campo real enviado por POST.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/indices-inflacion/")

    assert response.status_code == 200
    assert b'id="ec-indice-valor"' in response.data
    assert b'name="indice"' in response.data
    assert b'data-decimal="argentino"' in response.data
    assert b'inputmode="decimal"' in response.data


def test_inputs_asiento_debe_haber_declaran_money_ar_centavos():
    """
    Contrato: debe/haber usan formatter AR en vivo sin cambiar name de POST.

    El backend sigue recibiendo el mismo nombre de campo y normaliza a centavos.
    """
    contenido = Path(
        "app/contabilidad/templates/contabilidad/asientos_contables_nuevo.html"
    ).read_text(encoding="utf-8")

    assert contenido.count('data-money-ar="centavos"') == 2
    assert 'data-field="debe_centavos"' in contenido
    assert 'data-field="haber_centavos"' in contenido
    assert 'name="detalles[{{ renglon_idx }}][debe_centavos]"' in contenido
    assert 'name="detalles[{{ renglon_idx }}][haber_centavos]"' in contenido


def test_js_numero_argentino_convierte_punto_a_coma_sin_dom_inseguro():
    """
    Contrato: el punto decimal se transforma en coma desde JS global.

    Cubre punto normal, NumpadDecimal, beforeinput y pegado de texto.
    """
    contenido = Path("app/static/js/numero_argentino.js").read_text(
        encoding="utf-8"
    )

    assert 'input[data-decimal="argentino"]' in contenido
    assert "NumpadDecimal" in contenido
    assert 'evento.key === "."' in contenido
    assert 'evento.data === "."' in contenido
    assert 'input.setRangeText(",",' in contenido
    assert 'replaceAll(".", ",")' in contenido
    assert "normalizarPegadoDecimalArgentino" in contenido
    assert "innerHTML" not in contenido
    assert ".style" not in contenido
    assert 'setAttribute("style"' not in contenido


def test_js_money_ar_centavos_formatea_en_vivo():
    """
    Contrato: money AR acepta punto como decimal y formatea miles en vivo.

    Los campos dinamicos quedan cubiertos por delegacion de eventos global.
    """
    contenido = Path("app/static/js/numero_argentino.js").read_text(
        encoding="utf-8"
    )

    assert 'input[data-money-ar="centavos"]' in contenido
    assert "formatearMonedaArgentinaEnVivo" in contenido
    assert "formatearMonedaArgentinaCentavos" in contenido
    assert "normalizarPartesMonedaArgentina" in contenido
    assert "partesConEnteroInicial" in contenido
    assert 'parteEntera: partes.parteEntera || "0"' in contenido
    assert "obtenerIndiceSeparadorDecimal" in contenido
    assert "formatearMilesArgentinos" in contenido
    assert "setSelectionRange" in contenido
    assert "keydown" in contenido
    assert "beforeinput" in contenido
    assert "input" in contenido
    assert "paste" in contenido
    assert 'replace(/\\B(?=(\\d{3})+(?!\\d))/g, ".")' in contenido
    assert "innerHTML" not in contenido
    assert ".style" not in contenido
    assert 'setAttribute("style"' not in contenido


def test_js_numero_argentino_declara_contrato_global_cotizacion_ar():
    """
    Contrato: las cotizaciones argentinas viven en el asset global.

    El hook data-cotizacion-ar="1000000" maneja formato argentino con miles,
    hasta seis decimales y exporta normalizacion entera escalada para otros JS.
    """
    contenido = Path("app/static/js/numero_argentino.js").read_text(
        encoding="utf-8"
    )

    assert 'input[data-cotizacion-ar="1000000"]' in contenido
    assert "window.NeriSoftNumeroArgentino" in contenido
    assert "decimalArAEnteroEscala" in contenido
    assert "cotizacionArA1000000" in contenido
    assert "normalizarPartesCotizacionArgentina" in contenido
    assert "formatearCotizacionArgentinaEnVivo" in contenido
    assert "obtenerIndiceSeparadorDecimalCotizacion" in contenido
    assert "manejarKeydownCotizacionArgentina" in contenido
    assert "manejarBeforeInputCotizacionArgentina" in contenido
    assert "manejarInputCotizacionArgentina" in contenido
    assert "manejarPasteCotizacionArgentina" in contenido
    assert "inicializarCotizacionesArgentinas" in contenido
    assert "1000000" in contenido
    assert "innerHTML" not in contenido
    assert ".style" not in contenido
    assert 'setAttribute("style"' not in contenido
