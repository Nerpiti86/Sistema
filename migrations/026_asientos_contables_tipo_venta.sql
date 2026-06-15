PRAGMA foreign_keys = OFF;
PRAGMA legacy_alter_table = ON;

ALTER TABLE asientos_contables RENAME TO asientos_contables_legacy_026;

CREATE TABLE asientos_contables (
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
    CHECK (tipo IN ('MANUAL', 'AJUSTE', 'APERTURA', 'CIERRE', 'REVERSION', 'VENTA')),
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

INSERT INTO asientos_contables (
    id,
    ejercicio_id,
    numero_asiento,
    fecha,
    descripcion,
    estado,
    tipo,
    moneda_origen_codigo,
    moneda_destino_codigo,
    cotizacion_id,
    cotizacion_fecha,
    cotizacion_tipo,
    cotizacion_1000000,
    creado_en,
    actualizado_en,
    confirmado_en,
    anulado_en,
    asiento_reversion_id
)
SELECT
    id,
    ejercicio_id,
    numero_asiento,
    fecha,
    descripcion,
    estado,
    tipo,
    moneda_origen_codigo,
    moneda_destino_codigo,
    cotizacion_id,
    cotizacion_fecha,
    cotizacion_tipo,
    cotizacion_1000000,
    creado_en,
    actualizado_en,
    confirmado_en,
    anulado_en,
    asiento_reversion_id
FROM asientos_contables_legacy_026;

DROP TABLE asientos_contables_legacy_026;

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

PRAGMA legacy_alter_table = OFF;
PRAGMA foreign_keys = ON;
