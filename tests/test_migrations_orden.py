from pathlib import Path


def test_migrations_tienen_prefijo_numerico_unico_y_ordenado():
    """
    Contrato: las migraciones tienen un prefijo numerico unico y ordenado.

    Evita que dos archivos compitan por el mismo numero logico de version.
    """
    migrations = sorted(Path("migrations").glob("*.sql"))
    nombres = [migration.name for migration in migrations]
    prefijos = [nombre.split("_", maxsplit=1)[0] for nombre in nombres]

    assert nombres == [
        "001_schema_inicial.sql",
        "002_ejercicios_contables.sql",
        "003_cuentas_contables.sql",
        "004_coeficientes_inflacion.sql",
        "005_monedas.sql",
        "006_monedas_cotizaciones.sql",
        "007_asientos_contables.sql",
        "008_bancos.sql",
        "009_bancos_catalogo_inicial.sql",
        "010_bancos_codigo_alfanumerico_legacy.sql",
        "011_medios_operativos.sql",
        "012_catalogos_fiscales.sql",
        "013_grupos_clientes.sql",
        "014_paises.sql",
        "015_provincias.sql",
        "016_clientes.sql",
        "017_crear_articulos_venta.sql",
        "018_precio_sugerido_articulos_venta_centavos.sql",
        "019_clientes_cuenta_corriente_movimientos.sql",
    ]
    assert prefijos == [
        "001",
        "002",
        "003",
        "004",
        "005",
        "006",
        "007",
        "008",
        "009",
        "010",
        "011",
        "012",
        "013",
        "014",
        "015",
        "016",
        "017",
        "018",
        "019",
    ]
    assert len(prefijos) == len(set(prefijos))


def test_migrations_no_usan_current_timestamp_de_sqlite():
    """
    Contrato: las migraciones no definen CURRENT_TIMESTAMP.

    Los timestamps visibles/de usuario se cargan desde Python con datetime.now
    local, no desde SQLite UTC.
    """
    for migration in sorted(Path("migrations").glob("*.sql")):
        contenido = migration.read_text(encoding="utf-8")
        assert "CURRENT_TIMESTAMP" not in contenido


def test_migration_cuentas_ya_nace_con_booleanos_enteros():
    """
    Contrato: cuentas_contables nace con flags booleanos enteros.

    No debe existir una migracion posterior que pise la tabla para convertir
    SI/NO a 0/1.
    """
    contenido = Path("migrations/003_cuentas_contables.sql").read_text(
        encoding="utf-8"
    )

    assert "imputable INTEGER NOT NULL DEFAULT 0" in contenido
    assert "monetaria INTEGER NOT NULL DEFAULT 0" in contenido
    assert "imputable TEXT" not in contenido
    assert "monetaria TEXT" not in contenido
    assert "cuentas_contables_text_flags_backup" not in contenido
    assert "ALTER TABLE cuentas_contables RENAME" not in contenido


def test_migrador_registra_applied_at_con_datetime_now_local():
    """
    Contrato: schema_migrations tambien evita CURRENT_TIMESTAMP de SQLite.

    El timestamp de aplicacion se registra explicitamente desde Python.
    """
    contenido = Path("app/db.py").read_text(encoding="utf-8")

    assert "CURRENT_TIMESTAMP" not in contenido
    assert "from datetime import datetime" in contenido
    assert 'datetime.now().replace(microsecond=0).isoformat(sep=" ")' in contenido
    assert "INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)" in contenido
