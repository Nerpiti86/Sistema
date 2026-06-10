CREATE TABLE IF NOT EXISTS asientos_contables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejercicio_id INTEGER NOT NULL,
    numero_asiento INTEGER,
    fecha TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'BORRADOR',
    tipo TEXT NOT NULL DEFAULT 'MANUAL',
    moneda_origen_codigo TEXT NOT NULL DEFAULT 'ARS',
    moneda_destino_codigo TEXT NOT NULL DEFAULT 'ARS',
    cotizacion_id INTEGER,
    cotizacion_fecha TEXT NOT NULL,
    cotizacion_tipo TEXT NOT NULL DEFAULT 'CIERRE',
    cotizacion_1000000 INTEGER NOT NULL DEFAULT 1000000,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,
    confirmado_en TEXT,
    anulado_en TEXT,
    asiento_reversion_id INTEGER,

    FOREIGN KEY (ejercicio_id)
        REFERENCES ejercicios_contables(id),

    FOREIGN KEY (moneda_origen_codigo)
        REFERENCES monedas(codigo),

    FOREIGN KEY (moneda_destino_codigo)
        REFERENCES monedas(codigo),

    FOREIGN KEY (cotizacion_id)
        REFERENCES monedas_cotizaciones(id),

    FOREIGN KEY (asiento_reversion_id)
        REFERENCES asientos_contables(id),

    CHECK (estado IN ('BORRADOR', 'CONFIRMADO', 'ANULADO')),
    CHECK (tipo IN ('MANUAL', 'AJUSTE', 'APERTURA', 'CIERRE', 'REVERSION')),
    CHECK (cotizacion_tipo IN ('COMPRA', 'VENTA', 'CIERRE', 'PROMEDIO')),
    CHECK (cotizacion_1000000 > 0),
    CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    CHECK (cotizacion_fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    CHECK (CAST(substr(fecha, 6, 2) AS INTEGER) BETWEEN 1 AND 12),
    CHECK (CAST(substr(fecha, 9, 2) AS INTEGER) BETWEEN 1 AND 31),
    CHECK (CAST(substr(cotizacion_fecha, 6, 2) AS INTEGER) BETWEEN 1 AND 12),
    CHECK (CAST(substr(cotizacion_fecha, 9, 2) AS INTEGER) BETWEEN 1 AND 31),
    CHECK (
        moneda_origen_codigo != moneda_destino_codigo
        OR cotizacion_1000000 = 1000000
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_asientos_contables_numero_por_ejercicio
ON asientos_contables (ejercicio_id, numero_asiento)
WHERE numero_asiento IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_asientos_contables_ejercicio_fecha
ON asientos_contables (ejercicio_id, fecha);

CREATE INDEX IF NOT EXISTS ix_asientos_contables_estado
ON asientos_contables (estado);

CREATE INDEX IF NOT EXISTS ix_asientos_contables_monedas
ON asientos_contables (
    moneda_origen_codigo,
    moneda_destino_codigo,
    cotizacion_fecha,
    cotizacion_tipo
);

CREATE TABLE IF NOT EXISTS asientos_contables_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asiento_id INTEGER NOT NULL,
    renglon INTEGER NOT NULL,
    cuenta_contable_codigo TEXT NOT NULL,
    descripcion TEXT,
    moneda_codigo TEXT NOT NULL DEFAULT 'ARS',
    cotizacion_id INTEGER,
    cotizacion_fecha TEXT NOT NULL,
    cotizacion_tipo TEXT NOT NULL DEFAULT 'CIERRE',
    cotizacion_1000000 INTEGER NOT NULL DEFAULT 1000000,
    nominal_debe_centavos INTEGER NOT NULL DEFAULT 0,
    nominal_haber_centavos INTEGER NOT NULL DEFAULT 0,
    debe_centavos INTEGER NOT NULL DEFAULT 0,
    haber_centavos INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (asiento_id)
        REFERENCES asientos_contables(id)
        ON DELETE CASCADE,

    FOREIGN KEY (cuenta_contable_codigo)
        REFERENCES cuentas_contables(cuenta),

    FOREIGN KEY (moneda_codigo)
        REFERENCES monedas(codigo),

    FOREIGN KEY (cotizacion_id)
        REFERENCES monedas_cotizaciones(id),

    UNIQUE (asiento_id, renglon),

    CHECK (renglon > 0),
    CHECK (cotizacion_tipo IN ('COMPRA', 'VENTA', 'CIERRE', 'PROMEDIO')),
    CHECK (cotizacion_1000000 > 0),
    CHECK (cotizacion_fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    CHECK (CAST(substr(cotizacion_fecha, 6, 2) AS INTEGER) BETWEEN 1 AND 12),
    CHECK (CAST(substr(cotizacion_fecha, 9, 2) AS INTEGER) BETWEEN 1 AND 31),
    CHECK (nominal_debe_centavos >= 0),
    CHECK (nominal_haber_centavos >= 0),
    CHECK (debe_centavos >= 0),
    CHECK (haber_centavos >= 0),
    CHECK (
        (debe_centavos > 0 AND haber_centavos = 0)
        OR
        (debe_centavos = 0 AND haber_centavos > 0)
    ),
    CHECK (
        (nominal_debe_centavos > 0 AND nominal_haber_centavos = 0)
        OR
        (nominal_debe_centavos = 0 AND nominal_haber_centavos > 0)
    ),
    CHECK (
        moneda_codigo != 'ARS'
        OR cotizacion_1000000 = 1000000
    )
);

CREATE INDEX IF NOT EXISTS ix_asientos_contables_detalle_asiento
ON asientos_contables_detalle (asiento_id);

CREATE INDEX IF NOT EXISTS ix_asientos_contables_detalle_cuenta
ON asientos_contables_detalle (cuenta_contable_codigo);
