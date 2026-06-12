CREATE TABLE IF NOT EXISTS medios_operativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    requiere_cotizacion INTEGER NOT NULL DEFAULT 0,
    cotizacion_default_centavos INTEGER,
    banco_codigo TEXT,
    plaza TEXT,
    sucursal TEXT,
    numero_cuenta TEXT,
    cuenta_contable_codigo TEXT NOT NULL,
    moneda_codigo TEXT NOT NULL,
    cuit TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (length(trim(codigo)) > 0),
    CHECK (length(trim(nombre)) > 0),
    CHECK (tipo IN ('BANCO_PROPIO', 'EFECTIVO', 'TARJETA', 'VALORES_CARTERA')),
    CHECK (requiere_cotizacion IN (0, 1)),
    CHECK (cotizacion_default_centavos IS NULL OR cotizacion_default_centavos >= 0),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0),

    FOREIGN KEY (banco_codigo) REFERENCES bancos(codigo),
    FOREIGN KEY (cuenta_contable_codigo) REFERENCES cuentas_contables(cuenta),
    FOREIGN KEY (moneda_codigo) REFERENCES monedas(codigo)
);

CREATE INDEX IF NOT EXISTS ix_medios_operativos_activo_orden
ON medios_operativos (activo, orden, codigo);

CREATE INDEX IF NOT EXISTS ix_medios_operativos_tipo
ON medios_operativos (tipo, activo, orden);
