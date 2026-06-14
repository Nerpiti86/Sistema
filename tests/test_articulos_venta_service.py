from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.articulos_venta_service import (
    activar_articulo_venta,
    actualizar_articulo_venta_desde_formulario,
    crear_articulo_venta_desde_formulario,
    desactivar_articulo_venta,
    normalizar_id_articulo_venta_desde_formulario,
    obtener_contexto_edicion_articulo_venta,
    obtener_contexto_formulario_articulo_venta,
    obtener_contexto_listado_articulos_venta,
)


def test_crear_articulo_venta_desde_formulario_normaliza_y_valida_moneda():
    """Valida alta service con normalizacion de formulario y moneda activa."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta_desde_formulario(
            {
                "nombre": " Consulta profesional ",
                "tipo": " servicio ",
                "moneda_codigo": " ars ",
                "precio_unitario_sugerido_centavos": "12.500,00",
                "activo": "1",
                "orden": "3",
                "observaciones": " Precio sugerido general. ",
            }
        )

    assert articulo["nombre"] == "Consulta profesional"
    assert articulo["tipo"] == "SERVICIO"
    assert articulo["moneda_codigo"] == "ARS"
    assert articulo["precio_unitario_sugerido_centavos"] == 1250000
    assert articulo["activo"] == 1
    assert articulo["esta_activo"] is True
    assert articulo["orden"] == 3
    assert articulo["observaciones"] == "Precio sugerido general."


def test_crear_articulo_venta_checkbox_ausente_inactivo():
    """Valida contrato HTML: checkbox ausente equivale a 0."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio checkbox",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
            }
        )

    assert articulo["activo"] == 0
    assert articulo["esta_activo"] is False


def test_service_rechaza_moneda_inactiva():
    """Valida regla funcional de moneda activa."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        get_db().execute("UPDATE monedas SET activa = 0 WHERE codigo = ?", ("ARS",))

        with pytest.raises(ValueError, match="moneda no existe o no esta activa"):
            crear_articulo_venta_desde_formulario(
                {
                    "nombre": "Servicio moneda inactiva",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                    "activo": "1",
                }
            )


def test_actualizar_articulo_venta_desde_formulario_valida_y_actualiza():
    """Valida actualizacion service con reglas funcionales minimas."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio original",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": "1",
            }
        )

        actualizado = actualizar_articulo_venta_desde_formulario(
            articulo["id"],
            {
                "nombre": "Producto actualizado",
                "tipo": "PRODUCTO",
                "moneda_codigo": "USD",
                "precio_unitario_sugerido_centavos": "5,00",
                "activo": "1",
                "orden": "8",
                "observaciones": "Actualizado.",
            },
        )

    assert actualizado["id"] == articulo["id"]
    assert actualizado["nombre"] == "Producto actualizado"
    assert actualizado["tipo"] == "PRODUCTO"
    assert actualizado["moneda_codigo"] == "USD"
    assert actualizado["precio_unitario_sugerido_centavos"] == 500
    assert actualizado["orden"] == 8
    assert actualizado["observaciones"] == "Actualizado."


def test_contextos_articulos_venta():
    """Valida contextos funcionales de listado, formulario y edicion."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        activo = crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio activo",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": "1",
            }
        )
        crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio inactivo",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
            }
        )

        contexto_listado = obtener_contexto_listado_articulos_venta()
        contexto_formulario = obtener_contexto_formulario_articulo_venta()
        contexto_edicion = obtener_contexto_edicion_articulo_venta(activo["id"])

    assert contexto_listado["cantidad_articulos_venta"] == 2
    assert contexto_listado["cantidad_articulos_venta_activos"] == 1
    assert contexto_formulario["articulo"]["activo"] == 1
    assert contexto_formulario["articulo"]["orden"] == 0
    assert contexto_formulario["articulo"]["precio_unitario_sugerido_argentina"] == "0,00"
    assert contexto_formulario["tipos_articulo_venta"] == ["PRODUCTO", "SERVICIO"]
    assert contexto_formulario["cantidad_tipos_articulo_venta"] == 2
    assert contexto_formulario["cantidad_monedas"] >= 1
    assert "cuentas_contables_imputables" in contexto_formulario
    assert contexto_edicion["articulo"]["id"] == activo["id"]



def test_service_normaliza_precio_sugerido_formato_argentino():
    """Valida conversion de importe visual argentino a centavos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio con precio argentino",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "precio_unitario_sugerido_centavos": "1.234,56",
                "activo": "1",
            }
        )
        contexto = obtener_contexto_edicion_articulo_venta(articulo["id"])

    assert articulo["precio_unitario_sugerido_centavos"] == 123456
    assert contexto["articulo"]["precio_unitario_sugerido_argentina"] == "1.234,56"


def test_service_rechaza_precio_sugerido_fuera_de_contrato_argentino():
    """Valida que el precio sugerido use contrato de importes argentinos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="formato argentino"):
            crear_articulo_venta_desde_formulario(
                {
                    "nombre": "Servicio precio invalido",
                    "tipo": "SERVICIO",
                    "moneda_codigo": "ARS",
                    "precio_unitario_sugerido_centavos": "123456",
                    "activo": "1",
                }
            )

def test_activar_desactivar_articulo_venta():
    """Valida baja logica por activar/desactivar desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        articulo = crear_articulo_venta_desde_formulario(
            {
                "nombre": "Servicio estado",
                "tipo": "SERVICIO",
                "moneda_codigo": "ARS",
                "activo": "1",
            }
        )

        desactivado = desactivar_articulo_venta(articulo["id"])
        activado = activar_articulo_venta(articulo["id"])

    assert desactivado["activo"] == 0
    assert desactivado["esta_activo"] is False
    assert activado["activo"] == 1
    assert activado["esta_activo"] is True


def test_normalizar_id_articulo_venta_desde_formulario():
    """Valida normalizacion de id recibida desde formularios."""
    assert normalizar_id_articulo_venta_desde_formulario(" 12 ") == 12

    with pytest.raises(ValueError, match="numerico"):
        normalizar_id_articulo_venta_desde_formulario("abc")

    with pytest.raises(ValueError, match="positivo"):
        normalizar_id_articulo_venta_desde_formulario("0")


def test_service_rechaza_articulo_inexistente_en_edicion():
    """Valida error funcional al pedir contexto de edicion inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No existe"):
            obtener_contexto_edicion_articulo_venta(999)


def test_service_articulos_venta_no_usa_sql_ni_get_db():
    """Valida que service delega persistencia al repository."""
    contenido = Path("app/gestion/articulos_venta_service.py").read_text(
        encoding="utf-8"
    )

    assert "get_db" not in contenido
    assert ".execute(" not in contenido
    assert "SELECT " not in contenido
    assert "INSERT " not in contenido
    assert "UPDATE " not in contenido
    assert "DELETE " not in contenido


def test_service_articulos_venta_no_define_reglas_futuras():
    """Valida que el service no fija reglas futuras de ventas."""
    contenido = Path("app/gestion/articulos_venta_service.py").read_text(
        encoding="utf-8"
    )

    assert "precio_cliente" not in contenido
    assert "ultimo_precio" not in contenido
    assert "comprobante" not in contenido
    assert "asiento" not in contenido
    assert "arca" not in contenido.lower()
