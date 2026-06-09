import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.ejercicios_contables_service import (
    obtener_contexto_ejercicio_contable_activo,
    resolver_ejercicio_contable_para_fecha_operacion,
    validar_operacion_en_ejercicio_contable,
)


def _insertar_ejercicio_contable_service_para_test(
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


def test_resolver_ejercicio_contable_para_fecha_operacion_devuelve_activo_operable():
    """Valida resolucion de ejercicio activo y operable por fecha."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_service_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
            fase_cierre="ABIERTO",
            bloqueado=0,
        )

        ejercicio_contable = resolver_ejercicio_contable_para_fecha_operacion(
            "2026-06-09"
        )

    assert ejercicio_contable["codigo"] == "EJ2026"


def test_resolver_ejercicio_contable_para_fecha_operacion_rechaza_fecha_sin_ejercicio():
    """Valida que no se invente ejercicio para fechas sin rango contable."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe ejercicio contable activo"):
            resolver_ejercicio_contable_para_fecha_operacion("2026-06-09")


def test_resolver_ejercicio_contable_para_fecha_operacion_rechaza_inactivo():
    """Valida que una fecha dentro de un ejercicio inactivo no sea operable."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_service_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=0,
        )

        with pytest.raises(ValueError, match="no esta activo para operaciones"):
            resolver_ejercicio_contable_para_fecha_operacion("2026-06-09")


def test_validar_operacion_en_ejercicio_contable_acepta_fecha_y_codigo_operable():
    """Valida que una operacion pase solo con ejercicio activo y operable."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_service_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
            fase_cierre="EN_CIERRE",
            bloqueado=0,
        )

        resultado_validacion = validar_operacion_en_ejercicio_contable(
            "2026-06-09",
            "EJ2026",
        )

    assert resultado_validacion is True


def test_validar_operacion_en_ejercicio_contable_rechaza_codigo_inexistente():
    """Valida que el service no permita operar contra un codigo inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe el ejercicio contable"):
            validar_operacion_en_ejercicio_contable("2026-06-09", "EJ9999")


def test_validar_operacion_en_ejercicio_contable_rechaza_fecha_fuera_de_rango():
    """Valida que el service respete rango fecha_desde/fecha_hasta."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_service_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
        )

        with pytest.raises(ValueError, match="no pertenece"):
            validar_operacion_en_ejercicio_contable("2027-01-01", "EJ2026")


def test_validar_operacion_en_ejercicio_contable_rechaza_bloqueado():
    """Valida que el service bloquee operaciones en ejercicio bloqueado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_service_para_test(
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
            validar_operacion_en_ejercicio_contable("2026-06-09", "EJ2026")


def test_obtener_contexto_ejercicio_contable_activo_devuelve_contexto_minimo():
    """Valida contexto chico para rutas futuras sin cargar datos operativos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        _insertar_ejercicio_contable_service_para_test(
            db,
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            activo=1,
            fase_cierre="ABIERTO",
            bloqueado=0,
        )

        contexto_ejercicio_contable = obtener_contexto_ejercicio_contable_activo()

    assert contexto_ejercicio_contable["ejercicio_contable_codigo"] == "EJ2026"
    assert contexto_ejercicio_contable["ejercicio_contable_estado"] == "ABIERTO"
    assert contexto_ejercicio_contable["ejercicio_contable_fase_cierre"] == "ABIERTO"
    assert contexto_ejercicio_contable["ejercicio_contable_bloqueado"] is False
