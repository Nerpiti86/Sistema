import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.asientos_contables_repository import (
    crear_asiento_contable,
    listar_asientos_contables_por_ejercicio,
    obtener_asiento_contable_por_id,
)


def _crear_app():
    """Crea app de test para validar repository de asientos contables."""
    return create_app(TestConfig)


def _crear_ejercicio(db) -> int:
    db.execute(
        """
        INSERT INTO ejercicios_contables (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            creado_en,
            fase_cierre,
            bloqueado,
            es_primer_ejercicio
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "2026",
            "Ejercicio repository asientos",
            "2026-01-01",
            "2026-12-31",
            "ABIERTO",
            1,
            "2026-01-01 00:00:00",
            "ABIERTO",
            0,
            1,
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def _crear_cuenta(db, cuenta: str = "1.1.01.01.999") -> str:
    db.execute(
        """
        INSERT INTO cuentas_contables (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cuenta,
            f"Cuenta test {cuenta}",
            "DEBE",
            "PATRIMONIAL",
            1,
            1,
            "2026-01-01 00:00:00",
        ),
    )

    return cuenta


def _crear_cotizacion_usd_ars(db) -> int:
    db.execute(
        """
        INSERT INTO monedas_cotizaciones (
            moneda_origen_codigo,
            moneda_destino_codigo,
            fecha,
            tipo,
            cotizacion_1000000,
            fuente,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "USD",
            "ARS",
            "2026-06-10",
            "CIERRE",
            1250500000,
            "Manual",
            "2026-06-10 10:00:00",
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def _datos_asiento_base(ejercicio_id: int) -> dict:
    return {
        "ejercicio_id": ejercicio_id,
        "fecha": "2026-06-10",
        "descripcion": "Asiento repository",
        "moneda_origen_codigo": "ARS",
        "moneda_destino_codigo": "ARS",
        "cotizacion_fecha": "2026-06-10",
        "cotizacion_1000000": 1000000,
    }


def test_crear_asiento_ars_devuelve_cabecera_y_detalle_normalizados():
    """Valida alta repository de asiento ARS puro."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        asiento = crear_asiento_contable(
            _datos_asiento_base(ejercicio_id),
            [
                {
                    "cuenta_contable_codigo": cuenta,
                    "moneda_codigo": "ARS",
                    "nominal_debe_centavos": 10000,
                    "debe_centavos": 10000,
                }
            ],
        )

    assert asiento["id"] > 0
    assert asiento["estado"] == "BORRADOR"
    assert asiento["tipo"] == "MANUAL"
    assert asiento["moneda_destino_codigo"] == "ARS"
    assert len(asiento["detalles"]) == 1
    assert asiento["detalles"][0]["renglon"] == 1
    assert asiento["detalles"][0]["moneda_codigo"] == "ARS"
    assert asiento["detalles"][0]["nominal_debe_centavos"] == 10000
    assert asiento["detalles"][0]["debe_centavos"] == 10000


def test_crear_asiento_usd_ars_con_nominal_por_renglon():
    """Valida renglones con moneda real distinta y contabilidad en ARS."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta_usd = _crear_cuenta(db, "1.1.01.01.998")
        cuenta_ars = _crear_cuenta(db, "1.1.01.01.997")
        cotizacion_id = _crear_cotizacion_usd_ars(db)

        asiento = crear_asiento_contable(
            {
                "ejercicio_id": ejercicio_id,
                "fecha": "2026-06-10",
                "descripcion": "Compra USD",
                "moneda_origen_codigo": "USD",
                "moneda_destino_codigo": "ARS",
                "cotizacion_id": cotizacion_id,
                "cotizacion_fecha": "2026-06-10",
                "cotizacion_tipo": "CIERRE",
                "cotizacion_1000000": 1250500000,
            },
            [
                {
                    "cuenta_contable_codigo": cuenta_usd,
                    "descripcion": "Banco USD",
                    "moneda_codigo": "USD",
                    "cotizacion_id": cotizacion_id,
                    "cotizacion_fecha": "2026-06-10",
                    "cotizacion_tipo": "CIERRE",
                    "cotizacion_1000000": 1250500000,
                    "nominal_debe_centavos": 10000,
                    "debe_centavos": 12505000,
                },
                {
                    "cuenta_contable_codigo": cuenta_ars,
                    "descripcion": "Banco ARS",
                    "moneda_codigo": "ARS",
                    "nominal_haber_centavos": 12505000,
                    "haber_centavos": 12505000,
                },
            ],
        )

    assert asiento["moneda_origen_codigo"] == "USD"
    assert asiento["moneda_destino_codigo"] == "ARS"
    assert asiento["cotizacion_id"] == cotizacion_id
    assert asiento["detalles"][0]["moneda_codigo"] == "USD"
    assert asiento["detalles"][0]["nominal_debe_centavos"] == 10000
    assert asiento["detalles"][0]["debe_centavos"] == 12505000
    assert asiento["detalles"][1]["moneda_codigo"] == "ARS"
    assert asiento["detalles"][1]["nominal_haber_centavos"] == 12505000
    assert asiento["detalles"][1]["haber_centavos"] == 12505000


def test_obtener_asiento_por_id_devuelve_detalle_ordenado():
    """Valida lectura puntual de asiento con detalle ordenado por renglon."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        creado = crear_asiento_contable(
            _datos_asiento_base(ejercicio_id),
            [
                {
                    "renglon": 2,
                    "cuenta_contable_codigo": cuenta,
                    "nominal_haber_centavos": 10000,
                    "haber_centavos": 10000,
                },
                {
                    "renglon": 1,
                    "cuenta_contable_codigo": cuenta,
                    "nominal_debe_centavos": 10000,
                    "debe_centavos": 10000,
                },
            ],
        )

        recuperado = obtener_asiento_contable_por_id(creado["id"])

    assert recuperado is not None
    assert [detalle["renglon"] for detalle in recuperado["detalles"]] == [1, 2]


def test_obtener_asiento_inexistente_devuelve_none():
    """Valida respuesta nula ante id inexistente."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        asiento = obtener_asiento_contable_por_id(999999)

    assert asiento is None


def test_listar_asientos_por_ejercicio_respeta_limite_y_orden():
    """Valida listado acotado de cabeceras por ejercicio."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        crear_asiento_contable(
            {
                **_datos_asiento_base(ejercicio_id),
                "fecha": "2026-06-09",
                "descripcion": "Asiento viejo",
            },
            [
                {
                    "cuenta_contable_codigo": cuenta,
                    "nominal_debe_centavos": 10000,
                    "debe_centavos": 10000,
                }
            ],
        )
        crear_asiento_contable(
            {
                **_datos_asiento_base(ejercicio_id),
                "fecha": "2026-06-10",
                "descripcion": "Asiento nuevo",
            },
            [
                {
                    "cuenta_contable_codigo": cuenta,
                    "nominal_haber_centavos": 10000,
                    "haber_centavos": 10000,
                }
            ],
        )

        asientos = listar_asientos_contables_por_ejercicio(ejercicio_id, 1)

    assert len(asientos) == 1
    assert asientos[0]["fecha"] == "2026-06-10"
    assert "detalles" not in asientos[0]


def test_repository_rechaza_fecha_invalida():
    """Valida fecha real ISO en cabecera."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable(
                {
                    **_datos_asiento_base(ejercicio_id),
                    "fecha": "2026-02-31",
                },
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    }
                ],
            )


def test_repository_rechaza_moneda_destino_distinta_de_ars():
    """Valida que la contabilidad quede expresada siempre en ARS."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable(
                {
                    **_datos_asiento_base(ejercicio_id),
                    "moneda_destino_codigo": "USD",
                },
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "moneda_codigo": "USD",
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    }
                ],
            )


def test_repository_rechaza_renglon_ars_con_cotizacion_distinta_de_uno():
    """Valida consistencia de nominal ARS en renglones."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable(
                _datos_asiento_base(ejercicio_id),
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "moneda_codigo": "ARS",
                        "cotizacion_1000000": 1250500000,
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    }
                ],
            )


def test_repository_rechaza_lado_nominal_distinto_del_lado_contable():
    """Valida que nominal y contable imputen en el mismo lado."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable(
                _datos_asiento_base(ejercicio_id),
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_haber_centavos": 10000,
                        "debe_centavos": 10000,
                    }
                ],
            )


def test_repository_hace_rollback_si_falla_detalle():
    """Valida atomicidad: si falla un renglon no queda cabecera huerfana."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable(
                _datos_asiento_base(ejercicio_id),
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    },
                    {
                        "cuenta_contable_codigo": "1.1.01.01.996",
                        "nominal_haber_centavos": 10000,
                        "haber_centavos": 10000,
                    },
                ],
            )

        cantidad = db.execute(
            "SELECT COUNT(*) AS cantidad FROM asientos_contables"
        ).fetchone()["cantidad"]

    assert cantidad == 0
