import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.ejercicios_contables_repository import (
    listar_ejercicios_contables,
    obtener_ejercicio_contable_activo,
    obtener_ejercicio_contable_por_codigo,
    obtener_ejercicio_contable_por_fecha,
    validar_ejercicio_contable_operable,
    validar_fecha_dentro_de_ejercicio_contable,
)


def _insertar_ejercicio_contable_para_test(
    db,
    codigo,
    nombre,
    fecha_desde,
    fecha_hasta,
    estado="ABIERTO",
    activo=0,
    fase_cierre="ABIERTO",
    bloqueado=0,
    es_primer_ejercicio=0,
):
    db.execute(
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
            es_primer_ejercicio
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            fase_cierre,
            bloqueado,
            es_primer_ejercicio,
        ),
    )


def test_listar_ejercicios_contables_devuelve_filas_normalizadas():
    """Valida listado chico y normalizacion explicita de ejercicios_contables."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
            es_primer_ejercicio=1,
        )

        ejercicios_contables = listar_ejercicios_contables()

    assert len(ejercicios_contables) == 1
    assert ejercicios_contables[0]["codigo"] == "EJ2026"
    assert ejercicios_contables[0]["estado_codigo"] == "ABIERTO"
    assert ejercicios_contables[0]["fase_cierre_codigo"] == "ABIERTO"
    assert ejercicios_contables[0]["es_activo"] is True
    assert ejercicios_contables[0]["esta_bloqueado"] is False
    assert ejercicios_contables[0]["es_primer_ejercicio_bool"] is True


def test_obtener_ejercicio_contable_activo_devuelve_unico_activo():
    """Valida obtencion directa del ejercicio activo sin filtrar listas en Python."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2025",
            "Ejercicio 2025",
            "2025-01-01",
            "2025-12-31",
            activo=0,
        )
        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
        )

        ejercicio_contable_activo = obtener_ejercicio_contable_activo()

    assert ejercicio_contable_activo["codigo"] == "EJ2026"
    assert ejercicio_contable_activo["es_activo"] is True


def test_obtener_ejercicio_contable_activo_rechaza_faltante():
    """Valida que no se asuma un ejercicio activo inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="unico ejercicio contable activo"):
            obtener_ejercicio_contable_activo()


def test_obtener_ejercicio_contable_por_codigo_devuelve_none_si_no_existe():
    """Valida busqueda puntual por codigo sin cargar todos los ejercicios."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        ejercicio_contable = obtener_ejercicio_contable_por_codigo("EJ9999")

    assert ejercicio_contable is None


def test_obtener_ejercicio_contable_por_fecha_devuelve_ejercicio_del_rango():
    """Valida resolucion de ejercicio contable por fecha de operacion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
        )

        ejercicio_contable = obtener_ejercicio_contable_por_fecha("2026-06-09")

    assert ejercicio_contable is not None
    assert ejercicio_contable["codigo"] == "EJ2026"


def test_obtener_ejercicio_contable_por_fecha_rechaza_rangos_superpuestos():
    """Valida deteccion de ambiguedad con LIMIT 2 y bajo consumo de RAM."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
        )
        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2026_B",
            "Ejercicio 2026 B",
            "2026-06-01",
            "2026-06-30",
            activo=0,
        )

        with pytest.raises(ValueError, match="mas de un ejercicio contable"):
            obtener_ejercicio_contable_por_fecha("2026-06-09")


def test_validar_fecha_dentro_de_ejercicio_contable_rechaza_fecha_fuera_de_rango():
    """Valida que una operacion no pueda usar fecha fuera del ejercicio."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
        )

        with pytest.raises(ValueError, match="no pertenece"):
            validar_fecha_dentro_de_ejercicio_contable("2027-01-01", "EJ2026")


def test_validar_ejercicio_contable_operable_acepta_abierto_no_bloqueado():
    """Valida la condicion SQL minima para permitir operaciones futuras."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            estado="ABIERTO",
            activo=1,
            fase_cierre="EN_CIERRE",
            bloqueado=0,
        )

        resultado_validacion = validar_ejercicio_contable_operable("EJ2026")

    assert resultado_validacion is True


def test_validar_ejercicio_contable_operable_rechaza_bloqueado():
    """Valida que un ejercicio bloqueado no permita operaciones."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            estado="ABIERTO",
            activo=1,
            fase_cierre="BLOQUEADO",
            bloqueado=1,
        )

        with pytest.raises(ValueError, match="no permite operaciones"):
            validar_ejercicio_contable_operable("EJ2026")
