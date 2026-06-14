import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations
from app.gestion.articulos_venta_repository import (
    actualizar_articulo_venta_por_id,
    cambiar_estado_articulo_venta,
    crear_articulo_venta,
    listar_articulos_venta,
    listar_articulos_venta_activos,
    obtener_articulo_venta_por_id,
)


def test_crear_articulo_venta_minimo_devuelve_fila_normalizada():
    """Valida alta minima y normalizacion basica del repository."""
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
    assert articulo["moneda_codigo"] == "ARS"
    assert articulo["moneda_nombre"] == "Peso argentino"
    assert articulo["precio_unitario_sugerido_1000000"] == 0
    assert articulo["activo"] == 1
    assert articulo["orden"] == 0
    assert articulo["esta_activo"] is True


def test_crear_articulo_venta_con_precio_y_observaciones():
    """Valida campos opcionales sin fijar reglas futuras de venta."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta(
            {
                "nombre": "Producto odontologico",
                "tipo": "PRODUCTO",
                "moneda_codigo": "ARS",
                "precio_unitario_sugerido_1000000": "12500000000",
                "activo": "1",
                "orden": "5",
                "observaciones": "Precio general sugerido.",
            }
        )

    assert articulo["tipo"] == "PRODUCTO"
    assert articulo["precio_unitario_sugerido_1000000"] == 12500000000
    assert articulo["cuenta_ingreso_codigo"] is None
    assert articulo["cuenta_ingreso_descripcion"] is None
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
    """Valida listado de productos o servicios activos."""
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
                "cuenta_ingreso_codigo": None,
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
    assert actualizado["cuenta_ingreso_codigo"] is None
    assert actualizado["activo"] == 0
    assert actualizado["orden"] == 8
    assert actualizado["observaciones"] == "Actualizado."
    assert actualizado["actualizado_en"] is not None


def test_cambiar_estado_articulo_venta():
    """Valida baja logica sin borrado fisico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta(
            {
                "nombre": "Servicio desactivable",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
            }
        )

        desactivado = cambiar_estado_articulo_venta(articulo["id"], 0)

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


def test_repository_convierte_duplicado_en_value_error():
    """Valida error funcional ante nombre duplicado."""
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
