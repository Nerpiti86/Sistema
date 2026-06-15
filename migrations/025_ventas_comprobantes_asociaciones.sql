CREATE TABLE IF NOT EXISTS ventas_comprobantes_asociaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comprobante_id INTEGER NOT NULL,
    comprobante_asociado_id INTEGER NOT NULL,
    tipo_relacion TEXT NOT NULL DEFAULT 'MODIFICA',
    creado_en TEXT NOT NULL,

    CONSTRAINT fk_ventas_comprobantes_asoc_comprobante
        FOREIGN KEY (comprobante_id)
        REFERENCES ventas_comprobantes(id),

    CONSTRAINT fk_ventas_comprobantes_asoc_asociado
        FOREIGN KEY (comprobante_asociado_id)
        REFERENCES ventas_comprobantes(id),

    CONSTRAINT ck_ventas_comprobantes_asoc_distintos
        CHECK (comprobante_id <> comprobante_asociado_id),

    CONSTRAINT ck_ventas_comprobantes_asoc_tipo
        CHECK (tipo_relacion IN ('MODIFICA')),

    CONSTRAINT ck_ventas_comprobantes_asoc_creado_en
        CHECK (length(trim(creado_en)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ventas_comprobantes_asoc_comprobante
ON ventas_comprobantes_asociaciones (comprobante_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ventas_comprobantes_asoc_par
ON ventas_comprobantes_asociaciones (comprobante_id, comprobante_asociado_id);

CREATE INDEX IF NOT EXISTS ix_ventas_comprobantes_asoc_asociado
ON ventas_comprobantes_asociaciones (comprobante_asociado_id);
