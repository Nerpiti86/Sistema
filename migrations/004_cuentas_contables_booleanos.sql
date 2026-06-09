ALTER TABLE cuentas_contables RENAME TO cuentas_contables_text_flags_backup;

CREATE TABLE cuentas_contables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    saldo_habitual TEXT NOT NULL,
    naturaleza TEXT NOT NULL,
    imputable INTEGER NOT NULL DEFAULT 0,
    monetaria INTEGER NOT NULL DEFAULT 0,
    sumarizadora TEXT,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
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

INSERT INTO cuentas_contables (
    id,
    cuenta,
    descripcion,
    saldo_habitual,
    naturaleza,
    imputable,
    monetaria,
    sumarizadora,
    creado_en,
    actualizado_en
)
SELECT
    id,
    cuenta,
    descripcion,
    saldo_habitual,
    naturaleza,
    CASE
        WHEN UPPER(CAST(imputable AS TEXT)) IN ('1', 'SI', 'TRUE', 'ON') THEN 1
        ELSE 0
    END AS imputable,
    CASE
        WHEN UPPER(CAST(monetaria AS TEXT)) IN ('1', 'SI', 'TRUE', 'ON') THEN 1
        ELSE 0
    END AS monetaria,
    sumarizadora,
    creado_en,
    actualizado_en
FROM cuentas_contables_text_flags_backup;

DROP TABLE cuentas_contables_text_flags_backup;

CREATE INDEX IF NOT EXISTS ix_cuentas_contables_sumarizadora
ON cuentas_contables (sumarizadora);

CREATE INDEX IF NOT EXISTS ix_cuentas_contables_naturaleza
ON cuentas_contables (naturaleza);

CREATE INDEX IF NOT EXISTS ix_cuentas_contables_imputable
ON cuentas_contables (imputable);

CREATE INDEX IF NOT EXISTS ix_cuentas_contables_monetaria
ON cuentas_contables (monetaria);
