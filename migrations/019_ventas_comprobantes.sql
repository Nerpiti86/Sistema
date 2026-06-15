CREATE TABLE IF NOT EXISTS ventas_comprobantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    fecha_vencimiento TEXT,
    tipo_comprobante TEXT NOT NULL,
    letra TEXT NOT NULL DEFAULT 'X',
    punto_venta INTEGER NOT NULL DEFAULT 0,
    numero INTEGER NOT NULL DEFAULT 0,
    moneda_codigo TEXT NOT NULL DEFAULT 'ARS',
    cotizacion_centavos INTEGER NOT NULL DEFAULT 100,
    subtotal_centavos INTEGER NOT NULL DEFAULT 0,
    descuento_centavos INTEGER NOT NULL DEFAULT 0,
    recargo_centavos INTEGER NOT NULL DEFAULT 0,
    iva_centavos INTEGER NOT NULL DEFAULT 0,
    total_centavos INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'BORRADOR',
    asiento_id INTEGER,
    observaciones TEXT,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,
    confirmado_en TEXT,
    anulado_en TEXT,

    CONSTRAINT fk_ventas_comprobantes_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id),

    CONSTRAINT fk_ventas_comprobantes_moneda
        FOREIGN KEY (moneda_codigo)
        REFERENCES monedas(codigo),

    CONSTRAINT fk_ventas_comprobantes_asiento
        FOREIGN KEY (asiento_id)
        REFERENCES asientos_contables(id),

    CONSTRAINT ck_ventas_comprobantes_fecha_iso
        CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),

    CONSTRAINT ck_ventas_comprobantes_fecha_mes_dia
        CHECK (
            CAST(substr(fecha, 6, 2) AS INTEGER) BETWEEN 1 AND 12
            AND CAST(substr(fecha, 9, 2) AS INTEGER) BETWEEN 1 AND 31
        ),

    CONSTRAINT ck_ventas_comprobantes_vencimiento_iso
        CHECK (
            fecha_vencimiento IS NULL
            OR fecha_vencimiento GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        ),

    CONSTRAINT ck_ventas_comprobantes_vencimiento_mes_dia
        CHECK (
            fecha_vencimiento IS NULL
            OR (
                CAST(substr(fecha_vencimiento, 6, 2) AS INTEGER) BETWEEN 1 AND 12
                AND CAST(substr(fecha_vencimiento, 9, 2) AS INTEGER) BETWEEN 1 AND 31
            )
        ),

    CONSTRAINT ck_ventas_comprobantes_tipo
        CHECK (tipo_comprobante IN ('FACTURA', 'NOTA_DEBITO', 'NOTA_CREDITO')),

    CONSTRAINT ck_ventas_comprobantes_letra_no_vacia
        CHECK (length(trim(letra)) > 0),

    CONSTRAINT ck_ventas_comprobantes_punto_venta
        CHECK (typeof(punto_venta) = 'integer' AND punto_venta >= 0),

    CONSTRAINT ck_ventas_comprobantes_numero
        CHECK (typeof(numero) = 'integer' AND numero >= 0),

    CONSTRAINT ck_ventas_comprobantes_moneda_codigo
        CHECK (moneda_codigo GLOB '[A-Z][A-Z][A-Z]'),

    CONSTRAINT ck_ventas_comprobantes_cotizacion
        CHECK (typeof(cotizacion_centavos) = 'integer' AND cotizacion_centavos > 0),

    CONSTRAINT ck_ventas_comprobantes_subtotal
        CHECK (typeof(subtotal_centavos) = 'integer' AND subtotal_centavos >= 0),

    CONSTRAINT ck_ventas_comprobantes_descuento
        CHECK (typeof(descuento_centavos) = 'integer' AND descuento_centavos >= 0),

    CONSTRAINT ck_ventas_comprobantes_recargo
        CHECK (typeof(recargo_centavos) = 'integer' AND recargo_centavos >= 0),

    CONSTRAINT ck_ventas_comprobantes_iva
        CHECK (typeof(iva_centavos) = 'integer' AND iva_centavos >= 0),

    CONSTRAINT ck_ventas_comprobantes_total
        CHECK (typeof(total_centavos) = 'integer' AND total_centavos >= 0),

    CONSTRAINT ck_ventas_comprobantes_total_consistente
        CHECK (
            total_centavos =
            subtotal_centavos - descuento_centavos + recargo_centavos + iva_centavos
        ),

    CONSTRAINT ck_ventas_comprobantes_estado
        CHECK (estado IN ('BORRADOR', 'CONFIRMADO', 'ANULADO'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ventas_comprobantes_numero
ON ventas_comprobantes (tipo_comprobante, letra, punto_venta, numero)
WHERE punto_venta > 0 AND numero > 0;

CREATE INDEX IF NOT EXISTS ix_ventas_comprobantes_cliente_fecha
ON ventas_comprobantes (cliente_id, fecha, id);

CREATE INDEX IF NOT EXISTS ix_ventas_comprobantes_cliente_estado_fecha
ON ventas_comprobantes (cliente_id, estado, fecha, id);

CREATE INDEX IF NOT EXISTS ix_ventas_comprobantes_moneda
ON ventas_comprobantes (moneda_codigo);

CREATE INDEX IF NOT EXISTS ix_ventas_comprobantes_asiento
ON ventas_comprobantes (asiento_id);

CREATE TABLE IF NOT EXISTS ventas_comprobantes_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comprobante_id INTEGER NOT NULL,
    articulo_venta_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    cantidad_1000000 INTEGER NOT NULL DEFAULT 1000000,
    precio_unitario_centavos INTEGER NOT NULL DEFAULT 0,
    descuento_centavos INTEGER NOT NULL DEFAULT 0,
    subtotal_centavos INTEGER NOT NULL DEFAULT 0,
    iva_centavos INTEGER NOT NULL DEFAULT 0,
    total_linea_centavos INTEGER NOT NULL DEFAULT 0,
    cuenta_ingreso_codigo TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT,

    CONSTRAINT fk_ventas_detalle_comprobante
        FOREIGN KEY (comprobante_id)
        REFERENCES ventas_comprobantes(id),

    CONSTRAINT fk_ventas_detalle_articulo
        FOREIGN KEY (articulo_venta_id)
        REFERENCES articulos_venta(id),

    CONSTRAINT fk_ventas_detalle_cuenta_ingreso
        FOREIGN KEY (cuenta_ingreso_codigo)
        REFERENCES cuentas_contables(cuenta),

    CONSTRAINT ck_ventas_detalle_descripcion_no_vacia
        CHECK (length(trim(descripcion)) > 0),

    CONSTRAINT ck_ventas_detalle_cantidad
        CHECK (typeof(cantidad_1000000) = 'integer' AND cantidad_1000000 > 0),

    CONSTRAINT ck_ventas_detalle_precio_unitario
        CHECK (typeof(precio_unitario_centavos) = 'integer' AND precio_unitario_centavos >= 0),

    CONSTRAINT ck_ventas_detalle_descuento
        CHECK (typeof(descuento_centavos) = 'integer' AND descuento_centavos >= 0),

    CONSTRAINT ck_ventas_detalle_subtotal
        CHECK (typeof(subtotal_centavos) = 'integer' AND subtotal_centavos >= 0),

    CONSTRAINT ck_ventas_detalle_iva
        CHECK (typeof(iva_centavos) = 'integer' AND iva_centavos >= 0),

    CONSTRAINT ck_ventas_detalle_total_linea
        CHECK (typeof(total_linea_centavos) = 'integer' AND total_linea_centavos >= 0),

    CONSTRAINT ck_ventas_detalle_total_consistente
        CHECK (total_linea_centavos = subtotal_centavos - descuento_centavos + iva_centavos),

    CONSTRAINT ck_ventas_detalle_orden
        CHECK (typeof(orden) = 'integer' AND orden >= 0)
);

CREATE INDEX IF NOT EXISTS ix_ventas_detalle_comprobante
ON ventas_comprobantes_detalle (comprobante_id, orden, id);

CREATE INDEX IF NOT EXISTS ix_ventas_detalle_articulo
ON ventas_comprobantes_detalle (articulo_venta_id);

CREATE INDEX IF NOT EXISTS ix_ventas_detalle_cuenta_ingreso
ON ventas_comprobantes_detalle (cuenta_ingreso_codigo);
