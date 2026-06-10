CREATE TABLE IF NOT EXISTS monedas_cotizaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moneda_origen_codigo TEXT NOT NULL,
    moneda_destino_codigo TEXT NOT NULL,
    fecha TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'CIERRE',
    cotizacion_1000000 INTEGER NOT NULL,
    fuente TEXT,
    observaciones TEXT,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    FOREIGN KEY (moneda_origen_codigo)
        REFERENCES monedas (codigo),

    FOREIGN KEY (moneda_destino_codigo)
        REFERENCES monedas (codigo),

    UNIQUE (moneda_origen_codigo, moneda_destino_codigo, fecha, tipo),

    CHECK (moneda_origen_codigo GLOB '[A-Z][A-Z][A-Z]'),
    CHECK (moneda_destino_codigo GLOB '[A-Z][A-Z][A-Z]'),
    CHECK (moneda_origen_codigo != moneda_destino_codigo),
    CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    CHECK (CAST(substr(fecha, 6, 2) AS INTEGER) BETWEEN 1 AND 12),
    CHECK (CAST(substr(fecha, 9, 2) AS INTEGER) BETWEEN 1 AND 31),
    CHECK (tipo IN ('COMPRA', 'VENTA', 'CIERRE', 'PROMEDIO')),
    CHECK (cotizacion_1000000 > 0)
);

CREATE INDEX IF NOT EXISTS ix_monedas_cotizaciones_fecha
ON monedas_cotizaciones (fecha);

CREATE INDEX IF NOT EXISTS ix_monedas_cotizaciones_par_fecha
ON monedas_cotizaciones (
    moneda_origen_codigo,
    moneda_destino_codigo,
    fecha
);

CREATE INDEX IF NOT EXISTS ix_monedas_cotizaciones_tipo
ON monedas_cotizaciones (tipo);
