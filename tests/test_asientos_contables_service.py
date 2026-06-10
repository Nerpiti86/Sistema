import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_borrador,
    listar_asientos_contables,
    obtener_asiento_contable,
    preparar_asiento_contable_borrador_desde_formulario,
)


def _crear_app():
    """Crea app de test para validar service de asientos contables."""
    return create_app(TestConfig)


def _crear_ejercicio(
    db,
    *,
    codigo: str = "2026",
    estado: str = "ABIERTO",
    bloqueado: int = 0,
) -> int:
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
            codigo,
            f"Ejercicio service asientos {codigo}",
            "2026-01-01",
            "2026-12-31",
            estado,
            1,
            "2026-01-01 00:00:00",
            "ABIERTO",
            bloqueado,
            1,
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def _crear_cuenta(
    db,
    cuenta: str = "1.1.01.01.999",
    *,
    imputable: int = 1,
) -> str:
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
            imputable,
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
        "descripcion": "Asiento service",
    }


def test_service_crea_asiento_borrador_balanceado_en_ars():
    """Valida creacion de asiento balanceado desde reglas de service."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta_debe = _crear_cuenta(db, "1.1.01.01.999")
        cuenta_haber = _crear_cuenta(db, "1.1.01.01.998")

        asiento = crear_asiento_contable_borrador(
            _datos_asiento_base(ejercicio_id),
            [
                {
                    "cuenta_contable_codigo": cuenta_debe,
                    "nominal_debe_centavos": 10000,
                    "debe_centavos": 10000,
                },
                {
                    "cuenta_contable_codigo": cuenta_haber,
                    "nominal_haber_centavos": 10000,
                    "haber_centavos": 10000,
                },
            ],
        )

    assert asiento["estado"] == "BORRADOR"
    assert asiento["moneda_destino_codigo"] == "ARS"
    assert asiento["cotizacion_1000000"] == 1000000
    assert len(asiento["detalles"]) == 2


def test_service_rechaza_asiento_desbalanceado():
    """Valida que el service no delegue asientos desbalanceados al repository."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta_debe = _crear_cuenta(db, "1.1.01.01.999")
        cuenta_haber = _crear_cuenta(db, "1.1.01.01.998")

        with pytest.raises(ValueError):
            crear_asiento_contable_borrador(
                _datos_asiento_base(ejercicio_id),
                [
                    {
                        "cuenta_contable_codigo": cuenta_debe,
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    },
                    {
                        "cuenta_contable_codigo": cuenta_haber,
                        "nominal_haber_centavos": 9000,
                        "haber_centavos": 9000,
                    },
                ],
            )


def test_service_rechaza_fecha_fuera_del_ejercicio():
    """Valida que fecha y ejercicio informado sean consistentes."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable_borrador(
                {
                    **_datos_asiento_base(ejercicio_id),
                    "fecha": "2027-01-01",
                },
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    },
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_haber_centavos": 10000,
                        "haber_centavos": 10000,
                    },
                ],
            )


def test_service_rechaza_ejercicio_cerrado():
    """Valida que no se creen asientos en ejercicios cerrados."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db, estado="CERRADO")
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable_borrador(
                _datos_asiento_base(ejercicio_id),
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    },
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_haber_centavos": 10000,
                        "haber_centavos": 10000,
                    },
                ],
            )


def test_service_rechaza_ejercicio_bloqueado():
    """Valida bloqueo contable antes de persistir asientos."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db, bloqueado=1)
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable_borrador(
                _datos_asiento_base(ejercicio_id),
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    },
                    {
                        "cuenta_contable_codigo": cuenta,
                        "nominal_haber_centavos": 10000,
                        "haber_centavos": 10000,
                    },
                ],
            )


def test_service_rechaza_cuenta_no_imputable():
    """Valida que el service controle imputabilidad de cada renglon."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta_no_imputable = _crear_cuenta(db, imputable=0)

        with pytest.raises(ValueError):
            crear_asiento_contable_borrador(
                _datos_asiento_base(ejercicio_id),
                [
                    {
                        "cuenta_contable_codigo": cuenta_no_imputable,
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 10000,
                    },
                    {
                        "cuenta_contable_codigo": cuenta_no_imputable,
                        "nominal_haber_centavos": 10000,
                        "haber_centavos": 10000,
                    },
                ],
            )


def test_service_resuelve_cotizacion_usd_en_cabecera_y_detalle():
    """Valida resolucion de ultima cotizacion disponible para moneda extranjera."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta_usd = _crear_cuenta(db, "1.1.01.01.999")
        cuenta_ars = _crear_cuenta(db, "1.1.01.01.998")
        cotizacion_id = _crear_cotizacion_usd_ars(db)

        asiento = crear_asiento_contable_borrador(
            {
                **_datos_asiento_base(ejercicio_id),
                "descripcion": "Compra USD",
                "moneda_origen_codigo": "USD",
            },
            [
                {
                    "cuenta_contable_codigo": cuenta_usd,
                    "moneda_codigo": "USD",
                    "nominal_debe_centavos": 10000,
                    "debe_centavos": 12505000,
                },
                {
                    "cuenta_contable_codigo": cuenta_ars,
                    "moneda_codigo": "ARS",
                    "nominal_haber_centavos": 12505000,
                    "haber_centavos": 12505000,
                },
            ],
        )

    assert asiento["moneda_origen_codigo"] == "USD"
    assert asiento["cotizacion_id"] == cotizacion_id
    assert asiento["cotizacion_1000000"] == 1250500000
    assert asiento["detalles"][0]["moneda_codigo"] == "USD"
    assert asiento["detalles"][0]["cotizacion_id"] == cotizacion_id
    assert asiento["detalles"][0]["cotizacion_1000000"] == 1250500000
    assert asiento["detalles"][1]["moneda_codigo"] == "ARS"
    assert asiento["detalles"][1]["cotizacion_id"] is None
    assert asiento["detalles"][1]["cotizacion_1000000"] == 1000000


def test_service_rechaza_moneda_extranjera_sin_cotizacion():
    """Valida que no se pueda crear asiento FX sin cotizacion disponible."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta = _crear_cuenta(db)

        with pytest.raises(ValueError):
            crear_asiento_contable_borrador(
                {
                    **_datos_asiento_base(ejercicio_id),
                    "moneda_origen_codigo": "USD",
                },
                [
                    {
                        "cuenta_contable_codigo": cuenta,
                        "moneda_codigo": "USD",
                        "nominal_debe_centavos": 10000,
                        "debe_centavos": 12505000,
                    },
                    {
                        "cuenta_contable_codigo": cuenta,
                        "moneda_codigo": "ARS",
                        "nominal_haber_centavos": 12505000,
                        "haber_centavos": 12505000,
                    },
                ],
            )


def test_service_obtener_y_listar_delegan_en_repository():
    """Valida funciones de lectura expuestas por service."""
    app = _crear_app()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _crear_ejercicio(db)
        cuenta_debe = _crear_cuenta(db, "1.1.01.01.999")
        cuenta_haber = _crear_cuenta(db, "1.1.01.01.998")

        asiento = crear_asiento_contable_borrador(
            _datos_asiento_base(ejercicio_id),
            [
                {
                    "cuenta_contable_codigo": cuenta_debe,
                    "nominal_debe_centavos": 10000,
                    "debe_centavos": 10000,
                },
                {
                    "cuenta_contable_codigo": cuenta_haber,
                    "nominal_haber_centavos": 10000,
                    "haber_centavos": 10000,
                },
            ],
        )

        obtenido = obtener_asiento_contable(asiento["id"])
        listado = listar_asientos_contables(ejercicio_id, 10)

    assert obtenido is not None
    assert obtenido["id"] == asiento["id"]
    assert len(obtenido["detalles"]) == 2
    assert [item["id"] for item in listado] == [asiento["id"]]



def test_service_parser_formulario_normaliza_cabecera_y_renglones():
    """
    Valida parser puro del formulario de nuevo asiento.

    Convierte valores de pantalla a enteros en centavos sin persistir ni usar
    repository.
    """
    datos_asiento, detalles_asiento = (
        preparar_asiento_contable_borrador_desde_formulario(
            {
                "ejercicio_id": "7",
                "fecha": "2026-06-10",
                "descripcion": " Asiento manual ",
                "tipo": "manual",
                "moneda_origen_codigo": "ars",
                "moneda_destino_codigo": "ARS",
                "cotizacion_tipo": "cierre",
                "detalles[0][cuenta_contable_codigo]": "1.1.01.01.999",
                "detalles[0][descripcion]": "Caja",
                "detalles[0][moneda_codigo]": "ars",
                "detalles[0][cotizacion_1000000]": "1,000000",
                "detalles[0][debe_centavos]": "1.000,00",
                "detalles[0][haber_centavos]": "",
                "detalles[1][cuenta_contable_codigo]": "4.1.01.01.999",
                "detalles[1][descripcion]": "Venta",
                "detalles[1][moneda_codigo]": "ARS",
                "detalles[1][cotizacion_1000000]": "1,000000",
                "detalles[1][debe_centavos]": "",
                "detalles[1][haber_centavos]": "1.000,00",
            }
        )
    )

    assert datos_asiento == {
        "ejercicio_id": 7,
        "fecha": "2026-06-10",
        "descripcion": "Asiento manual",
        "tipo": "MANUAL",
        "estado": "BORRADOR",
        "moneda_origen_codigo": "ARS",
        "moneda_destino_codigo": "ARS",
        "cotizacion_tipo": "CIERRE",
    }
    assert detalles_asiento == [
        {
            "cuenta_contable_codigo": "1.1.01.01.999",
            "descripcion": "Caja",
            "moneda_codigo": "ARS",
            "cotizacion_1000000": 1000000,
            "nominal_debe_centavos": 100000,
            "nominal_haber_centavos": 0,
            "debe_centavos": 100000,
            "haber_centavos": 0,
        },
        {
            "cuenta_contable_codigo": "4.1.01.01.999",
            "descripcion": "Venta",
            "moneda_codigo": "ARS",
            "cotizacion_1000000": 1000000,
            "nominal_debe_centavos": 0,
            "nominal_haber_centavos": 100000,
            "debe_centavos": 0,
            "haber_centavos": 100000,
        },
    ]


def test_service_parser_formulario_ignora_renglones_vacios():
    """
    Valida que el parser ignore filas vacias del formulario.

    Esto permite mantener renglones base visibles sin crear detalles nulos.
    """
    datos_asiento, detalles_asiento = (
        preparar_asiento_contable_borrador_desde_formulario(
            {
                "ejercicio_id": "7",
                "fecha": "2026-06-10",
                "descripcion": "Asiento con fila vacia",
                "detalles[0][cuenta_contable_codigo]": "1.1.01.01.999",
                "detalles[0][debe_centavos]": "500,00",
                "detalles[1][cuenta_contable_codigo]": "",
                "detalles[1][descripcion]": "",
                "detalles[1][debe_centavos]": "",
                "detalles[1][haber_centavos]": "",
            }
        )
    )

    assert datos_asiento["ejercicio_id"] == 7
    assert len(detalles_asiento) == 1
    assert detalles_asiento[0]["debe_centavos"] == 50000


def test_service_parser_formulario_rechaza_renglon_con_debe_y_haber():
    """
    Valida regla de pantalla antes de delegar creacion del asiento.

    Un mismo renglon no puede registrar importe en debe y haber a la vez.
    """
    with pytest.raises(ValueError, match="debe y haber simultaneamente"):
        preparar_asiento_contable_borrador_desde_formulario(
            {
                "ejercicio_id": "7",
                "fecha": "2026-06-10",
                "detalles[0][cuenta_contable_codigo]": "1.1.01.01.999",
                "detalles[0][debe_centavos]": "500,00",
                "detalles[0][haber_centavos]": "500,00",
            }
        )


def test_service_parser_formulario_rechaza_importe_invalido():
    """
    Valida que el parser no acepte importes fuera del formato argentino.

    La conversion queda centralizada antes del futuro POST.
    """
    with pytest.raises(ValueError, match="debe del renglon es invalido"):
        preparar_asiento_contable_borrador_desde_formulario(
            {
                "ejercicio_id": "7",
                "fecha": "2026-06-10",
                "detalles[0][cuenta_contable_codigo]": "1.1.01.01.999",
                "detalles[0][debe_centavos]": "500.00",
            }
        )
