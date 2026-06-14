CREATE TABLE articulos_venta_nueva (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL COLLATE NOCASE,
    tipo TEXT NOT NULL,
    moneda_codigo TEXT NOT NULL,
    precio_unitario_sugerido_centavos INTEGER NOT NULL DEFAULT 0,
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

INSERT INTO articulos_venta_nueva (
    id,
    nombre,
    tipo,
    moneda_codigo,
    precio_unitario_sugerido_centavos,
    cuenta_ingreso_codigo,
    activo,
    orden,
    observaciones,
    creado_en,
    actualizado_en
)
SELECT
    id,
    nombre,
    tipo,
    moneda_codigo,
    CAST(precio_unitario_sugerido_1000000 / 10000 AS INTEGER),
    cuenta_ingreso_codigo,
    activo,
    orden,
    observaciones,
    creado_en,
    actualizado_en
FROM articulos_venta;

DROP TABLE articulos_venta;

ALTER TABLE articulos_venta_nueva RENAME TO articulos_venta;

CREATE UNIQUE INDEX ux_articulos_venta_nombre
    ON articulos_venta(nombre);

CREATE INDEX ix_articulos_venta_activo_nombre
    ON articulos_venta(activo, nombre);

CREATE INDEX ix_articulos_venta_tipo
    ON articulos_venta(tipo);

CREATE INDEX ix_articulos_venta_moneda
    ON articulos_venta(moneda_codigo);

CREATE INDEX ix_articulos_venta_cuenta_ingreso
    ON articulos_venta(cuenta_ingreso_codigo);
