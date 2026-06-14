from pathlib import Path

import pytest

from app import create_app
from app.config import TestConfig
from app.db import apply_migrations, get_db
from app.gestion.clientes_service import (
    activar_cliente,
    actualizar_cliente_desde_formulario,
    crear_cliente_desde_formulario,
    desactivar_cliente,
    normalizar_id_cliente_desde_formulario,
    obtener_cliente_activo_por_id,
    obtener_contexto_detalle_cliente,
    obtener_contexto_clientes_activos,
    obtener_contexto_listado_clientes,
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


def _crear_pais(db, nombre="Argentina", codigo_iso="AR", activo=1) -> int:
    cursor = db.execute(
        """
        INSERT INTO paises (nombre, codigo_iso, activo, orden, creado_en)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nombre, codigo_iso, activo, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_provincia(db, pais_id: int, nombre="Santa Fe", activo=1) -> int:
    cursor = db.execute(
        """
        INSERT INTO provincias (pais_id, nombre, activo, orden, creado_en)
        VALUES (?, ?, ?, ?, ?)
        """,
        (pais_id, nombre, activo, 10, "2026-01-01 10:00:00"),
    )
    return int(cursor.lastrowid)


def _crear_cuenta_contable(db, cuenta: str, descripcion: str, imputable=1) -> str:
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
            imputable,
            0,
            None,
            "2026-01-01 10:00:00",
        ),
    )
    return cuenta


def test_crear_cliente_desde_formulario_valida_referencias_activas():
    """Valida alta service con normalizacion de formulario y referencias activas."""
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
            "Deudores test",
        )
        cuenta_anticipos = _crear_cuenta_contable(
            db,
            "2.1.01.01.997",
            "Anticipos test",
        )

        cliente = crear_cliente_desde_formulario(
            {
                "razon_social": " Cliente SA ",
                "nombre_fantasia": " Cliente Comercial ",
                "grupo_cliente_id": str(grupo_id),
                "pais_id": str(pais_id),
                "provincia_id": str(provincia_id),
                "condicion_iva_codigo": "5",
                "tipo_documento_fiscal_codigo": "80",
                "numero_documento_fiscal": "30700000001",
                "cuenta_deudores_ventas_codigo": cuenta_deudores,
                "cuenta_anticipo_clientes_codigo": cuenta_anticipos,
                "activo": "1",
                "orden": "3",
            }
        )

    assert cliente["razon_social"] == "Cliente SA"
    assert cliente["nombre_fantasia"] == "Cliente Comercial"
    assert cliente["grupo_cliente_id"] == grupo_id
    assert cliente["provincia_id"] == provincia_id
    assert cliente["pais_id"] == pais_id
    assert cliente["condicion_iva_codigo"] == "5"
    assert cliente["tipo_documento_fiscal_codigo"] == "80"
    assert cliente["esta_activo"] is True
    assert cliente["orden"] == 3


def test_crear_cliente_desde_formulario_checkbox_ausente_inactivo():
    """Valida contrato HTML: checkbox ausente equivale a 0."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())

        cliente = crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Checkbox",
                "grupo_cliente_id": str(grupo_id),
            }
        )

    assert cliente["activo"] == 0
    assert cliente["esta_activo"] is False


def test_service_rechaza_grupo_cliente_inactivo():
    """Valida regla funcional de grupo de clientes activo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db(), activo=0)

        with pytest.raises(ValueError, match="grupo de clientes no existe o no esta activo"):
            crear_cliente_desde_formulario(
                {
                    "razon_social": "Cliente Grupo Inactivo",
                    "grupo_cliente_id": str(grupo_id),
                    "activo": "1",
                }
            )


def test_service_rechaza_pais_inactivo():
    """Valida regla funcional de pais activo."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        pais_id = _crear_pais(db, activo=0)

        with pytest.raises(ValueError, match="pais no existe o no esta activo"):
            crear_cliente_desde_formulario(
                {
                    "razon_social": "Cliente Pais Inactivo",
                    "grupo_cliente_id": str(grupo_id),
                    "pais_id": str(pais_id),
                    "activo": "1",
                }
            )


def test_service_rechaza_provincia_inactiva():
    """Valida regla funcional de provincia activa."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        pais_id = _crear_pais(db)
        provincia_id = _crear_provincia(db, pais_id, activo=0)

        with pytest.raises(ValueError, match="provincia no existe o no esta activa"):
            crear_cliente_desde_formulario(
                {
                    "razon_social": "Cliente Provincia Inactiva",
                    "grupo_cliente_id": str(grupo_id),
                    "pais_id": str(pais_id),
                    "provincia_id": str(provincia_id),
                    "activo": "1",
                }
            )


def test_service_rechaza_provincia_de_otro_pais():
    """Valida consistencia funcional entre pais y provincia."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        argentina_id = _crear_pais(db, nombre="Argentina", codigo_iso="AR")
        uruguay_id = _crear_pais(db, nombre="Uruguay", codigo_iso="UY")
        provincia_uruguay_id = _crear_provincia(
            db,
            uruguay_id,
            nombre="Montevideo",
        )

        with pytest.raises(ValueError, match="no pertenece al pais"):
            crear_cliente_desde_formulario(
                {
                    "razon_social": "Cliente Provincia Otro Pais",
                    "grupo_cliente_id": str(grupo_id),
                    "pais_id": str(argentina_id),
                    "provincia_id": str(provincia_uruguay_id),
                    "activo": "1",
                }
            )


def test_service_rechaza_catalogo_fiscal_inactivo():
    """Valida reglas funcionales de catalogos fiscales activos."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        db.execute("UPDATE condiciones_iva SET activo = 0 WHERE codigo = ?", ("5",))
        db.execute("UPDATE tipos_documento SET activo = 0 WHERE codigo = ?", ("80",))

        with pytest.raises(ValueError, match="condicion frente al IVA"):
            crear_cliente_desde_formulario(
                {
                    "razon_social": "Cliente Condicion Inactiva",
                    "grupo_cliente_id": str(grupo_id),
                    "condicion_iva_codigo": "5",
                    "activo": "1",
                }
            )

        with pytest.raises(ValueError, match="tipo de documento"):
            crear_cliente_desde_formulario(
                {
                    "razon_social": "Cliente Tipo Documento Inactivo",
                    "grupo_cliente_id": str(grupo_id),
                    "tipo_documento_fiscal_codigo": "80",
                    "numero_documento_fiscal": "30700000001",
                    "activo": "1",
                }
            )


def test_service_rechaza_cuenta_no_imputable():
    """Valida que las cuentas contables del cliente sean imputables."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        cuenta_no_imputable = _crear_cuenta_contable(
            db,
            "1.1.01.01.997",
            "Cuenta no imputable test",
            imputable=0,
        )

        with pytest.raises(ValueError, match="cuenta contable no existe o no es imputable"):
            crear_cliente_desde_formulario(
                {
                    "razon_social": "Cliente Cuenta No Imputable",
                    "grupo_cliente_id": str(grupo_id),
                    "cuenta_deudores_ventas_codigo": cuenta_no_imputable,
                    "activo": "1",
                }
            )


def test_actualizar_cliente_desde_formulario_valida_y_actualiza():
    """Valida actualizacion service con reglas funcionales."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        db = get_db()
        grupo_id = _crear_grupo_cliente(db)
        cliente = crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Original",
                "grupo_cliente_id": str(grupo_id),
                "activo": "1",
            }
        )

        actualizado = actualizar_cliente_desde_formulario(
            cliente["id"],
            {
                "razon_social": "Cliente Actualizado",
                "nombre_fantasia": "Comercial",
                "grupo_cliente_id": str(grupo_id),
                "telefono": "3410000000",
                "activo": "1",
                "orden": "8",
            },
        )

    assert actualizado["id"] == cliente["id"]
    assert actualizado["razon_social"] == "Cliente Actualizado"
    assert actualizado["nombre_fantasia"] == "Comercial"
    assert actualizado["telefono"] == "3410000000"
    assert actualizado["orden"] == 8


def test_contextos_clientes_y_obtener_activo():
    """Valida contextos funcionales de listado, activos y detalle."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())
        activo = crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Activo",
                "grupo_cliente_id": str(grupo_id),
                "activo": "1",
            }
        )
        crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Inactivo",
                "grupo_cliente_id": str(grupo_id),
            }
        )

        contexto_listado = obtener_contexto_listado_clientes()
        contexto_activos = obtener_contexto_clientes_activos()
        contexto_detalle = obtener_contexto_detalle_cliente(activo["id"])
        cliente_activo = obtener_cliente_activo_por_id(activo["id"])

    assert contexto_listado["cantidad_clientes"] == 2
    assert contexto_listado["cantidad_clientes_activos"] == 1
    assert contexto_activos["cantidad_clientes"] == 1
    assert contexto_detalle["cliente"]["id"] == activo["id"]
    assert cliente_activo["id"] == activo["id"]


def test_activar_desactivar_cliente():
    """Valida baja logica por activar/desactivar desde service."""
    app = create_app(TestConfig)

    with app.app_context():
        apply_migrations()
        grupo_id = _crear_grupo_cliente(get_db())
        cliente = crear_cliente_desde_formulario(
            {
                "razon_social": "Cliente Estado",
                "grupo_cliente_id": str(grupo_id),
                "activo": "1",
            }
        )

        desactivado = desactivar_cliente(cliente["id"])
        activado = activar_cliente(cliente["id"])

    assert desactivado["activo"] == 0
    assert desactivado["esta_activo"] is False
    assert activado["activo"] == 1
    assert activado["esta_activo"] is True


def test_normalizar_id_cliente_desde_formulario():
    """Valida normalizacion de id recibida desde formularios."""
    assert normalizar_id_cliente_desde_formulario(" 12 ") == 12

    with pytest.raises(ValueError, match="numerico"):
        normalizar_id_cliente_desde_formulario("abc")

    with pytest.raises(ValueError, match="positivo"):
        normalizar_id_cliente_desde_formulario("0")


def test_service_clientes_no_usa_sql_ni_get_db():
    """Valida que service delega persistencia al repository."""
    contenido = Path("app/gestion/clientes_service.py").read_text(encoding="utf-8")

    assert "get_db" not in contenido
    assert ".execute(" not in contenido
    assert "SELECT " not in contenido
    assert "INSERT " not in contenido
    assert "UPDATE " not in contenido
    assert "DELETE " not in contenido


def test_service_clientes_no_define_cuenta_ingreso():
    """Valida que ingresos queden fuera del maestro clientes."""
    contenido = Path("app/gestion/clientes_service.py").read_text(encoding="utf-8")

    assert "cuenta_ingreso" not in contenido
