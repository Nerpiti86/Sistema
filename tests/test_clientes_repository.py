from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.clientes_repository import (
    actualizar_cliente_por_id,
    cambiar_estado_cliente,
    crear_cliente,
    listar_clientes,
    listar_clientes_activos,
    obtener_cliente_por_id,
    validar_cliente_activo,
)


def _crear_grupo_cliente(db, nombre="General", activo=1) -> int:
    cursor = db.execute(
        """
        INSERT INTO grupos_clientes (nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?)
        """,
        (nombre, activo, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_pais(db) -> int:
    cursor = db.execute(
        """
        INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Argentina", "AR", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_provincia(db, pais_id: int) -> int:
    cursor = db.execute(
        """
        INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?, ?)
        """,
        (pais_id, "Santa Fe", 1, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cuenta_contable(db, cuenta: str, descripcion: str) -> str:
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
            descripcion,
            "DEBE",
            "PATRIMONIAL",
            1,
            0,
            None,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def test_crear_cliente_inserta_y_devuelve_fila_normalizada():
    """Valida alta repository con FKs y campos derivados normalizados."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        pais_id = _crear_pais(db)
        provincia_id = _crear_provincia(db, pais_id)
        cuenta_deudores = _crear_cuenta_contable(
            db,
            "1.1.01.01.997",
            "Deudores por ventas test",
        )
        cuenta_anticipos = _crear_cuenta_contable(
            db,
            "2.1.01.01.997",
            "Anticipos de clientes test",
        )

        cliente = crear_cliente(
            {
                "razon_social": "  Cliente SA  ",
                "nombre_fantasia": "  Cliente Comercial  ",
                "grupo_cliente_id": str(grupo_id),
                "telefono": " 3410000000 ",
                "email": " cliente@example.com ",
                "domicilio": " Calle 123 ",
                "codigo_postal": " S2000 ",
                "ciudad": " Rosario ",
                "pais_id": str(pais_id),
                "provincia_id": str(provincia_id),
                "condicion_iva_codigo": "5",
                "tipo_documento_fiscal_codigo": "80",
                "numero_documento_fiscal": "30700000001",
                "cuenta_deudores_ventas_codigo": cuenta_deudores,
                "cuenta_anticipo_clientes_codigo": cuenta_anticipos,
                "activo": "1",
                "orden": "7",
                "observaciones": " Observacion ",
            }
        )

    assert cliente["id"] > 0
    assert cliente["razon_social"] == "Cliente SA"
    assert cliente["nombre_fantasia"] == "Cliente Comercial"
    assert cliente["grupo_cliente_id"] == grupo_id
    assert cliente["grupo_cliente_nombre"] == "General"
    assert cliente["pais_nombre"] == "Argentina"
    assert cliente["pais_descripcion"] == "Argentina (AR)"
    assert cliente["provincia_nombre"] == "Santa Fe"
    assert cliente["condicion_iva_descripcion"] == "Consumidor Final"
    assert cliente["tipo_documento_fiscal_descripcion"] == "CUIT"
    assert cliente["documento_fiscal_descripcion"] == "CUIT 30700000001"
    assert cliente["cuenta_deudores_ventas_descripcion"] == "Deudores por ventas test"
    assert cliente["cuenta_anticipo_clientes_descripcion"] == "Anticipos de clientes test"
    assert cliente["esta_activo"] is True
    assert cliente["orden"] == 7
    assert cliente["nombre_visible"] == "Cliente Comercial"
    assert cliente["descripcion_select"] == "Cliente Comercial"


def test_listar_clientes_ordena_activos_y_orden():
    """Valida orden operativo del listado general de clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        crear_cliente(
            {
                "razon_social": "Cliente Inactivo",
                "grupo_cliente_id": grupo_id,
                "activo": 0,
                "orden": 1,
            }
        )
        crear_cliente(
            {
                "razon_social": "Cliente Activo B",
                "grupo_cliente_id": grupo_id,
                "activo": 1,
                "orden": 20,
            }
        )
        crear_cliente(
            {
                "razon_social": "Cliente Activo A",
                "grupo_cliente_id": grupo_id,
                "activo": 1,
                "orden": 10,
            }
        )

        clientes = listar_clientes()

    assert [cliente["razon_social"] for cliente in clientes] == [
        "Cliente Activo A",
        "Cliente Activo B",
        "Cliente Inactivo",
    ]


def test_listar_clientes_activos_excluye_inactivos():
    """Valida listado operativo solo con clientes activos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        crear_cliente(
            {
                "razon_social": "Cliente Activo",
                "grupo_cliente_id": grupo_id,
                "activo": 1,
            }
        )
        crear_cliente(
            {
                "razon_social": "Cliente Inactivo",
                "grupo_cliente_id": grupo_id,
                "activo": 0,
            }
        )

        clientes = listar_clientes_activos()

    assert [cliente["razon_social"] for cliente in clientes] == ["Cliente Activo"]


def test_obtener_cliente_por_id_devuelve_none_si_no_existe():
    """Valida busqueda nula por id inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        cliente = obtener_cliente_por_id(999)

    assert cliente is None


def test_crear_cliente_rechaza_razon_social_vacia():
    """Valida normalizacion repository de razon_social obligatoria."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        with pytest.raises(ValueError, match="razon social"):
            crear_cliente({"razon_social": "   ", "grupo_cliente_id": grupo_id})


def test_crear_cliente_rechaza_grupo_inexistente():
    """Valida FK obligatoria contra grupos_clientes."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()

        with pytest.raises(ValueError, match="No se pudo crear el cliente"):
            crear_cliente({"razon_social": "Cliente sin grupo", "grupo_cliente_id": 999})


def test_crear_cliente_rechaza_provincia_sin_pais():
    """Valida regla de consistencia geografica antes de persistir."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        pais_id = _crear_pais(db)
        provincia_id = _crear_provincia(db, pais_id)

        with pytest.raises(ValueError, match="provincia"):
            crear_cliente(
                {
                    "razon_social": "Cliente Provincia Sin Pais",
                    "grupo_cliente_id": grupo_id,
                    "provincia_id": provincia_id,
                }
            )


def test_crear_cliente_rechaza_documento_fiscal_incompleto():
    """Valida que tipo y numero fiscal se informen juntos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        with pytest.raises(ValueError, match="documento fiscal"):
            crear_cliente(
                {
                    "razon_social": "Cliente sin numero",
                    "grupo_cliente_id": grupo_id,
                    "tipo_documento_fiscal_codigo": "80",
                }
            )

        with pytest.raises(ValueError, match="documento fiscal"):
            crear_cliente(
                {
                    "razon_social": "Cliente sin tipo",
                    "grupo_cliente_id": grupo_id,
                    "numero_documento_fiscal": "30700000001",
                }
            )


def test_crear_cliente_rechaza_documento_fiscal_duplicado():
    """Valida unicidad de documento fiscal desde repository."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        crear_cliente(
            {
                "razon_social": "Cliente Uno",
                "grupo_cliente_id": grupo_id,
                "tipo_documento_fiscal_codigo": "80",
                "numero_documento_fiscal": "30700000001",
            }
        )

        with pytest.raises(ValueError, match="No se pudo crear el cliente"):
            crear_cliente(
                {
                    "razon_social": "Cliente Dos",
                    "grupo_cliente_id": grupo_id,
                    "tipo_documento_fiscal_codigo": "80",
                    "numero_documento_fiscal": "30700000001",
                }
            )


def test_actualizar_cliente_por_id_actualiza_campos_mutables():
    """Valida actualizacion repository de campos mutables del cliente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        cliente = crear_cliente(
            {
                "razon_social": "Cliente Original",
                "grupo_cliente_id": grupo_id,
                "activo": 1,
                "orden": 5,
            }
        )

        actualizado = actualizar_cliente_por_id(
            cliente["id"],
            {
                "razon_social": "Cliente Actualizado",
                "nombre_fantasia": "Nombre Comercial",
                "grupo_cliente_id": grupo_id,
                "telefono": "3410000000",
                "email": "actualizado@example.com",
                "activo": 0,
                "orden": 9,
                "observaciones": "Actualizado",
            },
        )

    assert actualizado["id"] == cliente["id"]
    assert actualizado["razon_social"] == "Cliente Actualizado"
    assert actualizado["nombre_fantasia"] == "Nombre Comercial"
    assert actualizado["telefono"] == "3410000000"
    assert actualizado["email"] == "actualizado@example.com"
    assert actualizado["activo"] == 0
    assert actualizado["esta_activo"] is False
    assert actualizado["orden"] == 9
    assert actualizado["observaciones"] == "Actualizado"
    assert actualizado["actualizado_en"] is not None


def test_actualizar_cliente_por_id_rechaza_inexistente():
    """Valida rechazo de update sobre cliente inexistente."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        with pytest.raises(ValueError, match="No existe el cliente"):
            actualizar_cliente_por_id(
                999,
                {
                    "razon_social": "Cliente Inexistente",
                    "grupo_cliente_id": grupo_id,
                },
            )


def test_cambiar_estado_cliente():
    """Valida baja logica por activar/desactivar sin borrado fisico."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())
        cliente = crear_cliente(
            {
                "razon_social": "Cliente Estado",
                "grupo_cliente_id": grupo_id,
                "activo": 1,
            }
        )

        desactivado = cambiar_estado_cliente(cliente["id"], 0)
        activado = cambiar_estado_cliente(cliente["id"], 1)

    assert desactivado["activo"] == 0
    assert desactivado["esta_activo"] is False
    assert activado["activo"] == 1
    assert activado["esta_activo"] is True


def test_validar_cliente_activo():
    """Valida cliente existente y activo para operaciones futuras."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())
        cliente_activo = crear_cliente(
            {
                "razon_social": "Cliente Activo",
                "grupo_cliente_id": grupo_id,
                "activo": 1,
            }
        )
        cliente_inactivo = crear_cliente(
            {
                "razon_social": "Cliente Inactivo",
                "grupo_cliente_id": grupo_id,
                "activo": 0,
            }
        )

        resultado = validar_cliente_activo(cliente_activo["id"])

        with pytest.raises(ValueError, match="cliente no existe o no esta activo"):
            validar_cliente_activo(cliente_inactivo["id"])

        with pytest.raises(ValueError, match="cliente no existe o no esta activo"):
            validar_cliente_activo(999)

    assert resultado is True


def test_repository_clientes_no_define_cuenta_ingreso():
    """Valida que ingresos queden fuera del maestro clientes."""
    contenido = Path("app/gestion/clientes_repository.py").read_text(encoding="utf-8")

    assert "cuenta_ingreso" not in contenido
