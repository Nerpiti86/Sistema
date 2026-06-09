import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.contabilidad.cuentas_contables_repository import (
    actualizar_cuenta_contable_por_cuenta,
    crear_cuenta_contable,
    listar_cuentas_contables,
    listar_cuentas_contables_por_sumarizadora,
    obtener_cuenta_contable_por_cuenta,
    validar_cuenta_contable_imputable,
)


def _insertar_cuenta_contable_para_test(
    db,
    cuenta,
    descripcion,
    saldo_habitual="DEBE",
    naturaleza="PATRIMONIAL",
    imputable=0,
    monetaria=1,
    sumarizadora=None,
):
    db.execute(
        """
        INSERT INTO cuentas_contables (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            sumarizadora
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            sumarizadora,
        ),
    )


def _insertar_jerarquia_caja_ars_para_test(db):
    _insertar_cuenta_contable_para_test(
        db,
        "1.0.00.00.000",
        "ACTIVO",
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.00.00.000",
        "ACTIVO CORRIENTE",
        sumarizadora="1.0.00.00.000",
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.01.00.000",
        "CAJAS Y BANCOS",
        sumarizadora="1.1.00.00.000",
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.01.01.000",
        "CAJAS",
        sumarizadora="1.1.01.00.000",
    )
    _insertar_cuenta_contable_para_test(
        db,
        "1.1.01.01.001",
        "CAJA ARS",
        imputable=1,
        sumarizadora="1.1.01.01.000",
    )


def test_crear_cuenta_contable_inserta_y_devuelve_fila_normalizada():
    """Valida alta repository y retorno normalizado de la cuenta creada."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()

        cuenta_padre = crear_cuenta_contable(
            {
                "cuenta": "1.1.01.01.000",
                "descripcion": "CAJAS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": 0,
                "monetaria": 1,
                "sumarizadora": None,
            }
        )
        cuenta_hija = crear_cuenta_contable(
            {
                "cuenta": "1.1.01.01.001",
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": 1,
                "monetaria": 1,
                "sumarizadora": cuenta_padre["cuenta"],
            }
        )

    assert cuenta_hija["cuenta"] == "1.1.01.01.001"
    assert cuenta_hija["descripcion"] == "CAJA ARS"
    assert cuenta_hija["saldo_habitual"] == "DEBE"
    assert cuenta_hija["naturaleza"] == "PATRIMONIAL"
    assert cuenta_hija["imputable"] == 1
    assert cuenta_hija["monetaria"] == 1
    assert cuenta_hija["sumarizadora"] == "1.1.01.01.000"
    assert cuenta_hija["es_imputable"] is True
    assert cuenta_hija["es_monetaria"] is True
    assert cuenta_hija["tiene_sumarizadora"] is True


def test_crear_cuenta_contable_normaliza_espacios_y_opciones():
    """Valida normalizacion minima del repository antes del INSERT."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        cuenta_contable = crear_cuenta_contable(
            {
                "cuenta": " 1.1.01.01.001 ",
                "descripcion": "  CAJA ARS  ",
                "saldo_habitual": " debe ",
                "naturaleza": " patrimonial ",
                "imputable": 1,
                "monetaria": 1,
                "sumarizadora": "",
            }
        )

    assert cuenta_contable["cuenta"] == "1.1.01.01.001"
    assert cuenta_contable["descripcion"] == "CAJA ARS"
    assert cuenta_contable["saldo_habitual"] == "DEBE"
    assert cuenta_contable["naturaleza"] == "PATRIMONIAL"
    assert cuenta_contable["imputable"] == 1
    assert cuenta_contable["monetaria"] == 1
    assert cuenta_contable["sumarizadora"] is None


def test_crear_cuenta_contable_rechaza_descripcion_vacia():
    """Valida que no se inserte cuenta contable sin descripcion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="descripcion"):
            crear_cuenta_contable(
                {
                    "cuenta": "1.1.01.01.001",
                    "descripcion": " ",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": 1,
                    "monetaria": 1,
                    "sumarizadora": None,
                }
            )


def test_crear_cuenta_contable_rechaza_saldo_habitual_invalido():
    """Valida opcion cerrada de saldo habitual antes del INSERT."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="saldo habitual"):
            crear_cuenta_contable(
                {
                    "cuenta": "1.1.01.01.001",
                    "descripcion": "CAJA ARS",
                    "saldo_habitual": "AMBOS",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": 1,
                    "monetaria": 1,
                    "sumarizadora": None,
                }
            )


def test_crear_cuenta_contable_rechaza_sumarizadora_inexistente():
    """Valida que el alta respete la FK de sumarizadora por codigo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_cuenta_contable(
                {
                    "cuenta": "1.1.01.01.001",
                    "descripcion": "CAJA ARS",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": 1,
                    "monetaria": 1,
                    "sumarizadora": "1.1.01.01.000",
                }
            )


def test_crear_cuenta_contable_rechaza_cuenta_duplicada():
    """Valida que el alta respete cuenta como codigo unico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        datos_cuenta_contable = {
            "cuenta": "1.1.01.01.001",
            "descripcion": "CAJA ARS",
            "saldo_habitual": "DEBE",
            "naturaleza": "PATRIMONIAL",
            "imputable": 1,
            "monetaria": 1,
            "sumarizadora": None,
        }

        crear_cuenta_contable(datos_cuenta_contable)

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_cuenta_contable(datos_cuenta_contable)


def test_actualizar_cuenta_contable_por_cuenta_actualiza_campos_mutables():
    """Valida edicion repository sin modificar el codigo de cuenta."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        cuenta_actualizada = actualizar_cuenta_contable_por_cuenta(
            "1.1.01.01.001",
            {
                "descripcion": "CAJA PESOS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": 1,
                "monetaria": 0,
                "sumarizadora": "1.1.01.01.000",
            },
        )

    assert cuenta_actualizada["cuenta"] == "1.1.01.01.001"
    assert cuenta_actualizada["descripcion"] == "CAJA PESOS"
    assert cuenta_actualizada["saldo_habitual"] == "DEBE"
    assert cuenta_actualizada["naturaleza"] == "PATRIMONIAL"
    assert cuenta_actualizada["imputable"] == 1
    assert cuenta_actualizada["monetaria"] == 0
    assert cuenta_actualizada["sumarizadora"] == "1.1.01.01.000"
    assert cuenta_actualizada["es_imputable"] is True
    assert cuenta_actualizada["es_monetaria"] is False
    assert cuenta_actualizada["actualizado_en"] is not None


def test_actualizar_cuenta_contable_por_cuenta_permite_quitar_sumarizadora():
    """Valida edicion de sumarizadora nullable."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        cuenta_actualizada = actualizar_cuenta_contable_por_cuenta(
            "1.1.01.01.001",
            {
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": 1,
                "monetaria": 1,
                "sumarizadora": "",
            },
        )

    assert cuenta_actualizada["sumarizadora"] is None
    assert cuenta_actualizada["tiene_sumarizadora"] is False


def test_actualizar_cuenta_contable_por_cuenta_rechaza_inexistente():
    """Valida que no se actualice una cuenta contable inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe la cuenta contable"):
            actualizar_cuenta_contable_por_cuenta(
                "9.9.99.99.999",
                {
                    "descripcion": "NO EXISTE",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": 1,
                    "monetaria": 1,
                    "sumarizadora": "",
                },
            )


def test_actualizar_cuenta_contable_por_cuenta_rechaza_sumarizadora_inexistente():
    """Valida que la edicion respete la FK de sumarizadora por codigo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_cuenta_contable(
            {
                "cuenta": "1.1.01.01.001",
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": 1,
                "monetaria": 1,
                "sumarizadora": None,
            }
        )

        with pytest.raises(ValueError, match="No se pudo actualizar"):
            actualizar_cuenta_contable_por_cuenta(
                "1.1.01.01.001",
                {
                    "descripcion": "CAJA ARS",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": 1,
                    "monetaria": 1,
                    "sumarizadora": "1.1.01.01.000",
                },
            )


def test_actualizar_cuenta_contable_por_cuenta_rechaza_sumarizadora_igual():
    """Valida que una cuenta no pueda sumarizarse a si misma."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        crear_cuenta_contable(
            {
                "cuenta": "1.1.01.01.001",
                "descripcion": "CAJA ARS",
                "saldo_habitual": "DEBE",
                "naturaleza": "PATRIMONIAL",
                "imputable": 1,
                "monetaria": 1,
                "sumarizadora": None,
            }
        )

        with pytest.raises(ValueError, match="sumarizarse a si misma"):
            actualizar_cuenta_contable_por_cuenta(
                "1.1.01.01.001",
                {
                    "descripcion": "CAJA ARS",
                    "saldo_habitual": "DEBE",
                    "naturaleza": "PATRIMONIAL",
                    "imputable": 1,
                    "monetaria": 1,
                    "sumarizadora": "1.1.01.01.001",
                },
            )


def test_listar_cuentas_contables_devuelve_filas_normalizadas():
    """Valida listado chico y normalizacion explicita de cuentas_contables."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        cuentas_contables = listar_cuentas_contables()

    assert len(cuentas_contables) == 5
    assert cuentas_contables[0]["cuenta"] == "1.0.00.00.000"
    assert cuentas_contables[-1]["cuenta"] == "1.1.01.01.001"
    assert cuentas_contables[-1]["descripcion"] == "CAJA ARS"
    assert cuentas_contables[-1]["es_imputable"] is True
    assert cuentas_contables[-1]["es_monetaria"] is True
    assert cuentas_contables[-1]["tiene_sumarizadora"] is True


def test_obtener_cuenta_contable_por_cuenta_devuelve_fila_normalizada():
    """Valida busqueda puntual por cuenta sin cargar todo el maestro."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        cuenta_contable = obtener_cuenta_contable_por_cuenta("1.1.01.01.001")

    assert cuenta_contable is not None
    assert cuenta_contable["cuenta"] == "1.1.01.01.001"
    assert cuenta_contable["descripcion"] == "CAJA ARS"
    assert cuenta_contable["saldo_habitual"] == "DEBE"
    assert cuenta_contable["naturaleza"] == "PATRIMONIAL"
    assert cuenta_contable["imputable"] == 1
    assert cuenta_contable["monetaria"] == 1
    assert cuenta_contable["sumarizadora"] == "1.1.01.01.000"
    assert cuenta_contable["es_imputable"] is True


def test_obtener_cuenta_contable_por_cuenta_devuelve_none_si_no_existe():
    """Valida busqueda puntual inexistente sin excepcion artificial."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        cuenta_contable = obtener_cuenta_contable_por_cuenta("9.9.99.99.999")

    assert cuenta_contable is None


def test_obtener_cuenta_contable_por_cuenta_rechaza_formato_invalido():
    """Valida que repository no consulte codigos fuera del contrato."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="formato 9.9.99.99.999"):
            obtener_cuenta_contable_por_cuenta("1.1.1.01.001")


def test_listar_cuentas_contables_por_sumarizadora_devuelve_hijas_directas():
    """Valida lectura de hijas directas usando sumarizadora como codigo padre."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)
        _insertar_cuenta_contable_para_test(
            db,
            "1.1.01.01.002",
            "CAJA USD",
            imputable=1,
            sumarizadora="1.1.01.01.000",
        )

        cuentas_hijas = listar_cuentas_contables_por_sumarizadora(
            "1.1.01.01.000"
        )

    assert [cuenta["cuenta"] for cuenta in cuentas_hijas] == [
        "1.1.01.01.001",
        "1.1.01.01.002",
    ]


def test_validar_cuenta_contable_imputable_acepta_cuenta_imputable():
    """Valida condicion minima para permitir futuros movimientos contables."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        resultado_validacion = validar_cuenta_contable_imputable("1.1.01.01.001")

    assert resultado_validacion is True


def test_validar_cuenta_contable_imputable_rechaza_cuenta_no_imputable():
    """Valida que una cuenta no imputable no permita movimientos futuros."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_jerarquia_caja_ars_para_test(db)

        with pytest.raises(ValueError, match="no existe o no es imputable"):
            validar_cuenta_contable_imputable("1.1.01.01.000")
