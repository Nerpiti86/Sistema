CREATE TABLE articulos_venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL COLLATE NOCASE,
    tipo TEXT NOT NULL,
    moneda_codigo TEXT NOT NULL,
    precio_unitario_sugerido_centavos INTEGER NOT NULL DEFAULT 0,
    cotizacion_1000000 INTEGER NOT NULL DEFAULT 1000000,
    cuenta_ingreso_codigo TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CONSTRAINT ck_articulos_venta_nombre_no_vacio
        CHECK (length(trim(nombre)) > 0),

    CONSTRAINT ck_articulos_venta_tipo
        CHECK (tipo IN ('PRODUCTO', 'SERVICIO')),

    CONSTRAINT ck_articulos_venta_precio_sugerido_centavos_entero_no_negativo
        CHECK (
            typeof(precio_unitario_sugerido_centavos) = 'integer'
            AND precio_unitario_sugerido_centavos >= 0
        ),

    CONSTRAINT ck_articulos_venta_cotizacion
        CHECK (
            typeof(cotizacion_1000000) = 'integer'
            AND cotizacion_1000000 > 0
            AND (
                moneda_codigo != 'ARS'
                OR cotizacion_1000000 = 1000000
            )
        ),

    CONSTRAINT ck_articulos_venta_activo
        CHECK (activo IN (0, 1)),

    CONSTRAINT ck_articulos_venta_orden_no_negativo
        CHECK (
            typeof(orden) = 'integer'
            AND orden >= 0
        ),

    CONSTRAINT fk_articulos_venta_moneda
        FOREIGN KEY (moneda_codigo)
        REFERENCES monedas(codigo),

    CONSTRAINT fk_articulos_venta_cuenta_ingreso
        FOREIGN KEY (cuenta_ingreso_codigo)
        REFERENCES cuentas_contables(cuenta)
);

CREATE UNIQUE INDEX ux_articulos_venta_nombre
    ON articulos_venta(nombre);

CREATE INDEX ix_articulos_venta_activo_nombre
    ON articulos_venta(activo, nombre);

CREATE INDEX ix_articulos_venta_tipo
    ON articulos_venta(tipo);

CREATE INDEX ix_articulos_venta_moneda
    ON articulos_venta(moneda_codigo);

CREATE INDEX ix_articulos_venta_cotizacion
    ON articulos_venta(cotizacion_1000000);

CREATE INDEX ix_articulos_venta_cuenta_ingreso
    ON articulos_venta(cuenta_ingreso_codigo);
