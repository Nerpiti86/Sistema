import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.contabilidad.coeficientes_inflacion_service import (
    guardar_indice_inflacion_desde_formulario,
    obtener_contexto_indices_inflacion,
)


def test_service_guarda_indice_inflacion_desde_formulario():
    """Valida normalizacion de periodo e indice argentino a enteros."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        indice = guardar_indice_inflacion_desde_formulario(
            {
                "periodo": "04/2025",
                "indice": "1.234,5678",
            }
        )

    assert indice["periodo_yyyymm"] == 202504
    assert indice["indice_10000"] == 12_345_678
    assert indice["periodo_argentina"] == "04/2025"
    assert indice["indice_argentina"] == "1.234,5678"


def test_service_contexto_indices_inflacion_lista_ordenado():
    """Valida contexto de pantalla con indices ordenados y formateados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        guardar_indice_inflacion_desde_formulario(
            {
                "periodo": "05/2025",
                "indice": "1.300,0000",
            }
        )
        guardar_indice_inflacion_desde_formulario(
            {
                "periodo": "04/2025",
                "indice": "1.200,0000",
            }
        )

        contexto = obtener_contexto_indices_inflacion()

    assert contexto["cantidad_indices_inflacion"] == 2
    assert contexto["tiene_indices_inflacion"] is True
    assert [
        indice["periodo_argentina"]
        for indice in contexto["indices_inflacion"]
    ] == ["04/2025", "05/2025"]
    assert contexto["indices_inflacion"][0]["indice_argentina"] == "1.200,0000"


def test_service_actualiza_indice_inflacion_existente():
    """Valida que la carga del mismo periodo actualice el indice."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        guardar_indice_inflacion_desde_formulario(
            {
                "periodo": "04/2025",
                "indice": "1.200,0000",
            }
        )
        indice = guardar_indice_inflacion_desde_formulario(
            {
                "periodo": "04/2025",
                "indice": "1.250,0000",
            }
        )
        contexto = obtener_contexto_indices_inflacion()

    assert indice["periodo_yyyymm"] == 202504
    assert indice["indice_10000"] == 12_500_000
    assert len(contexto["indices_inflacion"]) == 1
    assert contexto["indices_inflacion"][0]["indice_argentina"] == "1.250,0000"


def test_service_rechaza_formulario_invalido_de_indices():
    """Valida errores claros para periodo e indice con formato invalido."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            guardar_indice_inflacion_desde_formulario(
                {
                    "periodo": "",
                    "indice": "1.200,0000",
                }
            )

        with pytest.raises(ValueError):
            guardar_indice_inflacion_desde_formulario(
                {
                    "periodo": "13/2025",
                    "indice": "1.200,0000",
                }
            )

        with pytest.raises(ValueError):
            guardar_indice_inflacion_desde_formulario(
                {
                    "periodo": "04/2025",
                    "indice": "1.200,00",
                }
            )
