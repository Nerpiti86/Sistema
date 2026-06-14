import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.articulos_venta_repository import (
    actualizar_articulo_venta_por_id,
    cambiar_estado_articulo_venta,
    crear_articulo_venta,
    listar_articulos_venta,
    listar_articulos_venta_activos,
    obtener_articulo_venta_por_id,
    validar_articulo_venta_activo,
)


def _crear_cuenta_contable_ingreso(db, cuenta: str = "4.1.01.01.996") -> str:
    """Crea una cuenta imputable de ingreso para pruebas de repository."""
    db.execute(
        """
        INSERT INTO cuentas_contables (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            sumarizadora,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cuenta,
            "Ingresos por ventas test",
            "HABER",
            "RESULTADO",
            1,
            0,
            None,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def test_crear_articulo_venta_minimo_devuelve_fila_normalizada():
    """Valida alta minima y normalizacion funcional del repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta(
            {
                "nombre": "Consulta profesional",
                "tipo": "servicio",
                "moneda_codigo": "ars",
            }
        )

    assert articulo["id"] > 0
    assert articulo["nombre"] == "Consulta profesional"
    assert articulo["tipo"] == "SERVICIO"
    assert articulo["tipo_descripcion"] == "Servicio"
    assert articulo["moneda_codigo"] == "ARS"
    assert articulo["moneda_nombre"] == "Peso argentino"
    assert articulo["precio_unitario_sugerido_1000000"] == 0
    assert articulo["activo"] == 1
    assert articulo["orden"] == 0
    assert articulo["esta_activo"] is True
    assert articulo["descripcion_select"] == "Consulta profesional"


def test_crear_articulo_venta_con_precio_cuenta_y_observaciones():
    """Valida campos opcionales de precio sugerido, cuenta y observaciones."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cuenta_ingreso = _crear_cuenta_contable_ingreso(get_db())

        articulo = crear_articulo_venta(
            {
                "nombre": "Producto odontologico",
                "tipo": "PRODUCTO",
                "moneda_codigo": "ARS",
                "precio_unitario_sugerido_1000000": "12500000000",
                "cuenta_ingreso_codigo": cuenta_ingreso,
                "activo": "1",
                "orden": "5",
                "observaciones": "Precio general sugerido.",
            }
        )

    assert articulo["tipo"] == "PRODUCTO"
    assert articulo["tipo_descripcion"] == "Producto"
    assert articulo["precio_unitario_sugerido_1000000"] == 12500000000
    assert articulo["cuenta_ingreso_codigo"] == cuenta_ingreso
    assert articulo["cuenta_ingreso_descripcion"] == "Ingresos por ventas test"
    assert articulo["orden"] == 5
    assert articulo["observaciones"] == "Precio general sugerido."


def test_listar_articulos_venta_ordena_activos_orden_nombre():
    """Valida orden estable para listados administrativos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_articulo_venta(
            {
                "nombre": "Zeta inactivo",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": 0,
                "orden": 1,
            }
        )
        crear_articulo_venta(
            {
                "nombre": "Beta activo",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": 1,
                "orden": 2,
            }
        )
        crear_articulo_venta(
            {
                "nombre": "Alfa activo",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": 1,
                "orden": 1,
            }
        )

        nombres = [articulo["nombre"] for articulo in listar_articulos_venta()]

    assert nombres == ["Alfa activo", "Beta activo", "Zeta inactivo"]


def test_listar_articulos_venta_activos_filtra_inactivos():
    """Valida listado minimo para selectores operativos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_articulo_venta(
            {
                "nombre": "Servicio activo",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": 1,
            }
        )
        crear_articulo_venta(
            {
                "nombre": "Servicio inactivo",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": 0,
            }
        )

        nombres = [articulo["nombre"] for articulo in listar_articulos_venta_activos()]

    assert nombres == ["Servicio activo"]


def test_obtener_articulo_venta_por_id_devuelve_none_si_no_existe():
    """Valida consulta inexistente sin excepcion funcional."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = obtener_articulo_venta_por_id(999)

    assert articulo is None


def test_actualizar_articulo_venta_por_id_actualiza_campos_mutables():
    """Valida actualizacion completa de campos editables del maestro."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cuenta_ingreso = _crear_cuenta_contable_ingreso(get_db())

        articulo = crear_articulo_venta(
            {
                "nombre": "Consulta",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
            }
        )

        actualizado = actualizar_articulo_venta_por_id(
            articulo["id"],
            {
                "nombre": "Consulta actualizada",
                "tipo": "PRODUCTO",
                "moneda_codigo": "USD",
                "precio_unitario_sugerido_1000000": 5000000,
                "cuenta_ingreso_codigo": cuenta_ingreso,
                "activo": 0,
                "orden": 8,
                "observaciones": "Actualizado.",
            },
        )

    assert actualizado["id"] == articulo["id"]
    assert actualizado["nombre"] == "Consulta actualizada"
    assert actualizado["tipo"] == "PRODUCTO"
    assert actualizado["moneda_codigo"] == "USD"
    assert actualizado["precio_unitario_sugerido_1000000"] == 5000000
    assert actualizado["cuenta_ingreso_codigo"] == cuenta_ingreso
    assert actualizado["activo"] == 0
    assert actualizado["orden"] == 8
    assert actualizado["observaciones"] == "Actualizado."
    assert actualizado["actualizado_en"] is not None


def test_cambiar_estado_articulo_venta_y_validar_activo():
    """Valida baja logica y contrato de articulo activo para operaciones."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta(
            {
                "nombre": "Servicio validable",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
            }
        )

        assert validar_articulo_venta_activo(articulo["id"]) is True

        desactivado = cambiar_estado_articulo_venta(articulo["id"], 0)

        with pytest.raises(ValueError, match="no existe o no esta activo"):
            validar_articulo_venta_activo(articulo["id"])

    assert desactivado["activo"] == 0
    assert desactivado["esta_activo"] is False
    assert desactivado["actualizado_en"] is not None


def test_repository_rechaza_datos_invalidos_antes_de_sql():
    """Valida normalizaciones y errores funcionales previos a persistencia."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="nombre"):
            crear_articulo_venta(
                {
                    "nombre": "   ",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                }
            )

        with pytest.raises(ValueError, match="tipo"):
            crear_articulo_venta(
                {
                    "nombre": "Tipo invalido",
                    "tipo": "OTRO",
                    "moneda_codigo": "ARS",
                }
            )

        with pytest.raises(ValueError, match="moneda"):
            crear_articulo_venta(
                {
                    "nombre": "Sin moneda",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "",
                }
            )

        with pytest.raises(ValueError, match="precio"):
            crear_articulo_venta(
                {
                    "nombre": "Precio invalido",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                    "precio_unitario_sugerido_1000000": "abc",
                }
            )

        with pytest.raises(ValueError, match="negativo"):
            crear_articulo_venta(
                {
                    "nombre": "Precio negativo",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                    "precio_unitario_sugerido_1000000": -1,
                }
            )

        with pytest.raises(ValueError, match="activo"):
            crear_articulo_venta(
                {
                    "nombre": "Activo invalido",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                    "activo": 2,
                }
            )

        with pytest.raises(ValueError, match="orden"):
            crear_articulo_venta(
                {
                    "nombre": "Orden invalido",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                    "orden": -1,
                }
            )


def test_repository_convierte_integrity_error_en_value_error():
    """Valida errores funcionales ante FKs invalidas o duplicados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        crear_articulo_venta(
            {
                "nombre": "Servicio unico",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
            }
        )

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_articulo_venta(
                {
                    "nombre": "servicio unico",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                }
            )

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_articulo_venta(
                {
                    "nombre": "Moneda inexistente",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "GBP",
                }
            )

        with pytest.raises(ValueError, match="No se pudo crear"):
            crear_articulo_venta(
                {
                    "nombre": "Cuenta inexistente",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                    "cuenta_ingreso_codigo": "9.9.99.99.999",
                }
            )


def test_repository_rechaza_ids_invalidos_o_inexistentes():
    """Valida contrato de ids positivos y existencia en updates/estado."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="numerico"):
            obtener_articulo_venta_por_id("abc")

        with pytest.raises(ValueError, match="positivo"):
            obtener_articulo_venta_por_id(0)

        with pytest.raises(ValueError, match="No existe"):
            actualizar_articulo_venta_por_id(
                999,
                {
                    "nombre": "Inexistente",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                },
            )

        with pytest.raises(ValueError, match="No existe"):
            cambiar_estado_articulo_venta(999, 1)
