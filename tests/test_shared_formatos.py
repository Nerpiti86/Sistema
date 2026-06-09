import pytest

from app.shared.formatos import (
    formatear_entero_escala_a_decimal_argentino,
    formatear_fecha_iso_a_argentina,
    formatear_periodo_yyyymm_a_argentina,
    normalizar_decimal_argentino_a_entero_escala,
    normalizar_fecha_argentina_a_iso,
    normalizar_periodo_argentino_a_yyyymm,
)


def test_formatea_y_normaliza_fecha_entre_bd_iso_y_pantalla_argentina():
    """Contrato: la BD guarda fecha ISO y la pantalla muestra DD/MM/YYYY."""
    assert formatear_fecha_iso_a_argentina("2025-11-01") == "01/11/2025"
    assert normalizar_fecha_argentina_a_iso("01/11/2025") == "2025-11-01"


def test_rechaza_fechas_con_formato_o_calendario_invalido():
    """Contrato: las fechas deben ser estrictas y validas en calendario real."""
    with pytest.raises(ValueError):
        formatear_fecha_iso_a_argentina("01/11/2025")

    with pytest.raises(ValueError):
        formatear_fecha_iso_a_argentina("2025-02-30")

    with pytest.raises(ValueError):
        normalizar_fecha_argentina_a_iso("2025-11-01")

    with pytest.raises(ValueError):
        normalizar_fecha_argentina_a_iso("31/02/2025")


def test_formatea_periodo_yyyymm_a_mes_anio_y_fecha_argentina():
    """Contrato: el periodo BD YYYYMM se muestra como MM/YYYY o 01/MM/YYYY."""
    assert formatear_periodo_yyyymm_a_argentina(202511) == "11/2025"
    assert formatear_periodo_yyyymm_a_argentina("202511") == "11/2025"
    assert (
        formatear_periodo_yyyymm_a_argentina(202511, como_fecha=True)
        == "01/11/2025"
    )


def test_normaliza_periodo_argentino_a_entero_yyyymm():
    """Contrato: el periodo visible vuelve al entero YYYYMM estable para BD."""
    assert normalizar_periodo_argentino_a_yyyymm("11/2025") == 202511
    assert normalizar_periodo_argentino_a_yyyymm("01/11/2025") == 202511


def test_rechaza_periodos_invalidos_o_fechas_que_no_representan_periodo():
    """Contrato: periodo mensual no acepta meses imposibles ni dias distintos de 01."""
    with pytest.raises(ValueError):
        formatear_periodo_yyyymm_a_argentina(202513)

    with pytest.raises(ValueError):
        normalizar_periodo_argentino_a_yyyymm("13/2025")

    with pytest.raises(ValueError):
        normalizar_periodo_argentino_a_yyyymm("15/11/2025")


def test_formatea_importe_entero_en_centavos_a_decimal_argentino():
    """Contrato: los importes se guardan enteros y se muestran con coma decimal."""
    assert (
        formatear_entero_escala_a_decimal_argentino(123456789, 2)
        == "1.234.567,89"
    )
    assert formatear_entero_escala_a_decimal_argentino(-123456789, 2) == (
        "-1.234.567,89"
    )


def test_normaliza_importe_argentino_a_entero_en_centavos():
    """Contrato: el importe visible vuelve a centavos sin usar float."""
    assert (
        normalizar_decimal_argentino_a_entero_escala("1.234.567,89", 2)
        == 123456789
    )
    assert (
        normalizar_decimal_argentino_a_entero_escala("-1.234.567,89", 2)
        == -123456789
    )


def test_formatea_indice_de_inflacion_escalado_a_cuatro_decimales():
    """Contrato: el indice se guarda escalado a 4 decimales y se muestra local."""
    assert (
        formatear_entero_escala_a_decimal_argentino(98413581, 4)
        == "9.841,3581"
    )
    assert (
        normalizar_decimal_argentino_a_entero_escala("9.841,3581", 4)
        == 98413581
    )


def test_formatea_coeficiente_escalado_sin_perder_precision_decimal():
    """Contrato: los coeficientes se muestran con coma decimal y escala explicita."""
    assert (
        formatear_entero_escala_a_decimal_argentino(1028452719346, 12)
        == "1,028452719346"
    )
    assert (
        normalizar_decimal_argentino_a_entero_escala("1,028452719346", 12)
        == 1028452719346
    )


def test_rechaza_decimales_con_escala_o_separadores_invalidos():
    """Contrato: no se aceptan importes ambiguos ni miles mal agrupados."""
    with pytest.raises(ValueError):
        normalizar_decimal_argentino_a_entero_escala("1,2", 2)

    with pytest.raises(ValueError):
        normalizar_decimal_argentino_a_entero_escala("12.34,56", 2)

    with pytest.raises(ValueError):
        normalizar_decimal_argentino_a_entero_escala("1.234,567", 2)
