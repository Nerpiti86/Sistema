from pathlib import Path


def test_repositories_no_usan_current_timestamp_para_campos_visibles():
    """
    Contrato: los timestamps visibles/de usuario se generan con datetime.now local.

    No se modifica schema ni migrations. Los repositories insertan/actualizan
    timestamps explicitamente cuando el campo se muestra en la aplicacion.
    """
    paths = [
        Path("app/contabilidad/coeficientes_inflacion_repository.py"),
        Path("app/contabilidad/cuentas_contables_repository.py"),
        Path("app/contabilidad/ejercicios_contables_repository.py"),
    ]

    for path in paths:
        contenido = path.read_text(encoding="utf-8")
        assert "CURRENT_TIMESTAMP" not in contenido
        assert 'datetime.now().replace(microsecond=0).isoformat(sep=" ")' in contenido


def test_ajuste_datetime_local_no_agrega_migration():
    """
    Contrato: este ajuste no agrega ni modifica migrations.

    El schema conserva sus defaults actuales; la correccion de datos existentes
    se realiza por UPDATE operativo controlado sobre la DB local.
    """
    migrations = sorted(Path("migrations").glob("*.sql"))

    assert migrations
    assert not Path("migrations/005_datetime_local.sql").exists()
    assert not Path("migrations/005_hora_local.sql").exists()

    for migration in migrations:
        contenido = migration.read_text(encoding="utf-8")
        assert "datetime.now()" not in contenido
        assert "America/Argentina/Buenos_Aires" not in contenido
