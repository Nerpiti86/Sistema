CREATE TABLE IF NOT EXISTS cuentas_contables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    saldo_habitual TEXT NOT NULL,
    naturaleza TEXT NOT NULL,
    imputable INTEGER NOT NULL DEFAULT 0,
    monetaria INTEGER NOT NULL DEFAULT 0,
    sumarizadora TEXT,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (cuenta GLOB '[0-9].[0-9].[0-9][0-9].[0-9][0-9].[0-9][0-9][0-9]'),
    CHECK (length(trim(descripcion)) > 0),
    CHECK (saldo_habitual IN ('DEBE', 'HABER')),
    CHECK (naturaleza IN ('PATRIMONIAL', 'RESULTADO')),
    CHECK (imputable IN (0, 1)),
    CHECK (monetaria IN (0, 1)),
    CHECK (sumarizadora IS NULL OR sumarizadora != cuenta),

    FOREIGN KEY (sumarizadora)
        REFERENCES cuentas_contables (cuenta)
);

CREATE INDEX IF NOT EXISTS ix_cuentas_contables_sumarizadora
ON cuentas_contables (sumarizadora);

CREATE INDEX IF NOT EXISTS ix_cuentas_contables_naturaleza
ON cuentas_contables (naturaleza);

CREATE INDEX IF NOT EXISTS ix_cuentas_contables_imputable
ON cuentas_contables (imputable);

CREATE INDEX IF NOT EXISTS ix_cuentas_contables_monetaria
ON cuentas_contables (monetaria);
