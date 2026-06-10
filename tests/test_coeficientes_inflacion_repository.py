import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.coeficientes_inflacion_repository import (
    guardar_indice_inflacion,
    listar_coeficientes_inflacion_por_ejercicio_id,
    listar_indices_inflacion,
    obtener_indice_inflacion,
    obtener_ultimo_indice_inflacion,
    reemplazar_coeficientes_inflacion_ejercicio,
)


def test_repository_guarda_y_obtiene_indice_inflacion():
    """Valida alta y lectura de indices mensuales enteros."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        indice = guardar_indice_inflacion(202501, 78641257)
        recuperado = obtener_indice_inflacion(202501)

    assert indice["periodo_yyyymm"] == 202501
    assert indice["indice_10000"] == 78641257
    assert recuperado == indice


def test_repository_actualiza_indice_existente_sin_duplicar_periodo():
    """Valida upsert de indices por periodo mensual unico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        guardar_indice_inflacion(202501, 78641257)
        actualizado = guardar_indice_inflacion(202501, 78641258)
        indices = listar_indices_inflacion()

    assert len(indices) == 1
    assert actualizado["periodo_yyyymm"] == 202501
    assert actualizado["indice_10000"] == 78641258
    assert actualizado["actualizado_en"] is not None


def test_repository_lista_indices_ordenados_y_obtiene_ultimo():
    """Valida orden cronologico y lectura del ultimo indice cargado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        guardar_indice_inflacion(202503, 80110000)
        guardar_indice_inflacion(202501, 78641257)
        guardar_indice_inflacion(202502, 79300000)

        indices = listar_indices_inflacion()
        ultimo = obtener_ultimo_indice_inflacion()

    assert [indice["periodo_yyyymm"] for indice in indices] == [
        202501,
        202502,
        202503,
    ]
    assert ultimo["periodo_yyyymm"] == 202503
    assert ultimo["indice_10000"] == 80110000


def test_repository_rechaza_indice_invalido_antes_de_sql():
    """Valida errores de entrada sin delegarlos a la base."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            guardar_indice_inflacion(202513, 78641257)

        with pytest.raises(ValueError):
            guardar_indice_inflacion(202501, 0)

        with pytest.raises(ValueError):
            guardar_indice_inflacion(202501, 10.5)


def test_repository_reemplaza_coeficientes_de_ejercicio():
    """Valida snapshot reemplazable de coeficientes por ejercicio contable."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        ejercicio_id = _crear_ejercicio_contable()

        coeficientes_iniciales = reemplazar_coeficientes_inflacion_ejercicio(
            ejercicio_id,
            [
                {
                    "periodo_yyyymm": 202501,
                    "indice_inicio_10000": 78641257,
                    "indice_cierre_periodo_yyyymm": 202512,
                    "indice_cierre_10000": 101213715,
                    "coeficiente_1000000000000": 1287030737568,
                },
                {
                    "periodo_yyyymm": 202502,
                    "indice_inicio_10000": 79300000,
                    "indice_cierre_periodo_yyyymm": 202512,
                    "indice_cierre_10000": 101213715,
                    "coeficiente_1000000000000": 1276349495586,
                },
            ],
        )

        coeficientes_reemplazados = reemplazar_coeficientes_inflacion_ejercicio(
            ejercicio_id,
            [
                {
                    "periodo_yyyymm": 202501,
                    "indice_inicio_10000": 78641257,
                    "indice_cierre_periodo_yyyymm": 202512,
                    "indice_cierre_10000": 101213715,
                    "coeficiente_1000000000000": 1287030737568,
                },
            ],
        )

        coeficientes_listados = listar_coeficientes_inflacion_por_ejercicio_id(
            ejercicio_id
        )

    assert len(coeficientes_iniciales) == 2
    assert len(coeficientes_reemplazados) == 1
    assert coeficientes_listados == coeficientes_reemplazados
    assert coeficientes_reemplazados[0]["periodo_yyyymm"] == 202501


def test_repository_rechaza_coeficientes_con_ejercicio_inexistente():
    """Valida integridad referencial desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError):
            reemplazar_coeficientes_inflacion_ejercicio(
                999,
                [
                    {
                        "periodo_yyyymm": 202501,
                        "indice_inicio_10000": 78641257,
                        "indice_cierre_periodo_yyyymm": 202512,
                        "indice_cierre_10000": 101213715,
                        "coeficiente_1000000000000": 1287030737568,
                    },
                ],
            )


def test_repository_rechaza_coeficientes_invalidos_antes_de_sql():
    """Valida que el repository solo acepte enteros positivos y periodos validos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        ejercicio_id = _crear_ejercicio_contable()

        with pytest.raises(ValueError):
            reemplazar_coeficientes_inflacion_ejercicio(
                ejercicio_id,
                [],
            )

        with pytest.raises(ValueError):
            reemplazar_coeficientes_inflacion_ejercicio(
                ejercicio_id,
                [
                    {
                        "periodo_yyyymm": 202513,
                        "indice_inicio_10000": 78641257,
                        "indice_cierre_periodo_yyyymm": 202512,
                        "indice_cierre_10000": 101213715,
                        "coeficiente_1000000000000": 1287030737568,
                    },
                ],
            )

        with pytest.raises(ValueError):
            reemplazar_coeficientes_inflacion_ejercicio(
                ejercicio_id,
                [
                    {
                        "periodo_yyyymm": 202501,
                        "indice_inicio_10000": 0,
                        "indice_cierre_periodo_yyyymm": 202512,
                        "indice_cierre_10000": 101213715,
                        "coeficiente_1000000000000": 1287030737568,
                    },
                ],
            )


def _crear_ejercicio_contable():
    cursor = get_db().execute(
        """
        INSERT INTO ejercicios_contables (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            fase_cierre,
            bloqueado,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "EJ2025",
            "Ejercicio 2025",
            "2025-01-01",
            "2025-12-31",
            "ABIERTO",
            1,
            "ABIERTO",
            0,
            "2026-01-01 10:00:00",
        ),
    )

    return cursor.lastrowid
