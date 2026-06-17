CREATE TABLE IF NOT EXISTS clientes_cobranzas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    tipo_cobranza TEXT NOT NULL,
    tipo_comprobante TEXT NOT NULL DEFAULT 'RECIBO',
    letra TEXT NOT NULL DEFAULT 'C',
    punto_venta INTEGER NOT NULL DEFAULT 0,
    numero INTEGER NOT NULL DEFAULT 0,
    moneda_codigo TEXT NOT NULL DEFAULT 'ARS',
    cotizacion_1000000 INTEGER NOT NULL DEFAULT 1000000,
    total_centavos INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'BORRADOR',
    asiento_id INTEGER,
    observaciones TEXT,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,
    confirmado_en TEXT,
    anulado_en TEXT,

    CONSTRAINT fk_clientes_cobranzas_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id),

    CONSTRAINT fk_clientes_cobranzas_moneda
        FOREIGN KEY (moneda_codigo)
        REFERENCES monedas(codigo),

    CONSTRAINT fk_clientes_cobranzas_asiento
        FOREIGN KEY (asiento_id)
        REFERENCES asientos_contables(id),

    CONSTRAINT ck_clientes_cobranzas_fecha_iso
        CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),

    CONSTRAINT ck_clientes_cobranzas_fecha_mes_dia
        CHECK (
            CAST(substr(fecha, 6, 2) AS INTEGER) BETWEEN 1 AND 12
            AND CAST(substr(fecha, 9, 2) AS INTEGER) BETWEEN 1 AND 31
        ),

    CONSTRAINT ck_clientes_cobranzas_tipo
        CHECK (tipo_cobranza IN ('APLICADA', 'ANTICIPO', 'MIXTA')),

    CONSTRAINT ck_clientes_cobranzas_tipo_comprobante
        CHECK (tipo_comprobante IN ('RECIBO')),

    CONSTRAINT ck_clientes_cobranzas_letra_no_vacia
        CHECK (length(trim(letra)) > 0),

    CONSTRAINT ck_clientes_cobranzas_punto_venta
        CHECK (typeof(punto_venta) = 'integer' AND punto_venta >= 0),

    CONSTRAINT ck_clientes_cobranzas_numero
        CHECK (typeof(numero) = 'integer' AND numero >= 0),

    CONSTRAINT ck_clientes_cobranzas_moneda_codigo
        CHECK (moneda_codigo GLOB '[A-Z][A-Z][A-Z]'),

    CONSTRAINT ck_clientes_cobranzas_cotizacion
        CHECK (typeof(cotizacion_1000000) = 'integer' AND cotizacion_1000000 > 0),

    CONSTRAINT ck_clientes_cobranzas_total
        CHECK (typeof(total_centavos) = 'integer' AND total_centavos >= 0),

    CONSTRAINT ck_clientes_cobranzas_estado
        CHECK (estado IN ('BORRADOR', 'CONFIRMADO', 'ANULADO')),

    CONSTRAINT ck_clientes_cobranzas_observaciones_no_vacias
        CHECK (observaciones IS NULL OR length(trim(observaciones)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_cobranzas_numero
ON clientes_cobranzas (tipo_comprobante, letra, punto_venta, numero)
WHERE punto_venta > 0 AND numero > 0;

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_cliente_fecha
ON clientes_cobranzas (cliente_id, fecha, id);

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_cliente_estado
ON clientes_cobranzas (cliente_id, estado, fecha, id);

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_asiento
ON clientes_cobranzas (asiento_id);

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_moneda
ON clientes_cobranzas (moneda_codigo);

CREATE TABLE IF NOT EXISTS clientes_cobranzas_lineas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cobranza_cliente_id INTEGER NOT NULL,
    tipo_linea TEXT NOT NULL,
    movimiento_ctacte_cancelado_id INTEGER,
    venta_comprobante_id INTEGER,
    movimiento_ctacte_generado_id INTEGER,
    importe_centavos INTEGER NOT NULL,
    cuenta_cancelacion_codigo TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT,

    CONSTRAINT fk_clientes_cobranzas_lineas_cobranza
        FOREIGN KEY (cobranza_cliente_id)
        REFERENCES clientes_cobranzas(id),

    CONSTRAINT fk_clientes_cobranzas_lineas_ctacte_cancelada
        FOREIGN KEY (movimiento_ctacte_cancelado_id)
        REFERENCES clientes_cuenta_corriente_movimientos(id),

    CONSTRAINT fk_clientes_cobranzas_lineas_comprobante
        FOREIGN KEY (venta_comprobante_id)
        REFERENCES ventas_comprobantes(id),

    CONSTRAINT fk_clientes_cobranzas_lineas_ctacte_generada
        FOREIGN KEY (movimiento_ctacte_generado_id)
        REFERENCES clientes_cuenta_corriente_movimientos(id),

    CONSTRAINT fk_clientes_cobranzas_lineas_cuenta
        FOREIGN KEY (cuenta_cancelacion_codigo)
        REFERENCES cuentas_contables(cuenta),

    CONSTRAINT ck_clientes_cobranzas_lineas_tipo
        CHECK (tipo_linea IN ('FACTURA', 'NOTA_DEBITO', 'ANTICIPO')),

    CONSTRAINT ck_clientes_cobranzas_lineas_importe
        CHECK (typeof(importe_centavos) = 'integer' AND importe_centavos > 0),

    CONSTRAINT ck_clientes_cobranzas_lineas_orden
        CHECK (typeof(orden) = 'integer' AND orden >= 0),

    CONSTRAINT ck_clientes_cobranzas_lineas_referencias
        CHECK (
            (
                tipo_linea = 'ANTICIPO'
                AND movimiento_ctacte_cancelado_id IS NULL
                AND venta_comprobante_id IS NULL
            )
            OR
            (
                tipo_linea IN ('FACTURA', 'NOTA_DEBITO')
                AND movimiento_ctacte_cancelado_id IS NOT NULL
                AND venta_comprobante_id IS NOT NULL
            )
        ),

    CONSTRAINT ck_clientes_cobranzas_lineas_observaciones_no_vacias
        CHECK (observaciones IS NULL OR length(trim(observaciones)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_cobranzas_lineas_orden
ON clientes_cobranzas_lineas (cobranza_cliente_id, orden);

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_lineas_cobranza
ON clientes_cobranzas_lineas (cobranza_cliente_id, id);

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_lineas_ctacte_cancelada
ON clientes_cobranzas_lineas (movimiento_ctacte_cancelado_id);

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_lineas_comprobante
ON clientes_cobranzas_lineas (venta_comprobante_id);

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_lineas_ctacte_generada
ON clientes_cobranzas_lineas (movimiento_ctacte_generado_id);

CREATE INDEX IF NOT EXISTS ix_clientes_cobranzas_lineas_cuenta
ON clientes_cobranzas_lineas (cuenta_cancelacion_codigo);

CREATE TABLE IF NOT EXISTS movimientos_caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    tipo_movimiento TEXT NOT NULL,
    origen_tipo TEXT,
    origen_id INTEGER,
    moneda_contable_codigo TEXT NOT NULL DEFAULT 'ARS',
    total_contable_centavos INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'BORRADOR',
    asiento_id INTEGER,
    observaciones TEXT,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,
    confirmado_en TEXT,
    anulado_en TEXT,

    CONSTRAINT fk_movimientos_caja_moneda_contable
        FOREIGN KEY (moneda_contable_codigo)
        REFERENCES monedas(codigo),

    CONSTRAINT fk_movimientos_caja_asiento
        FOREIGN KEY (asiento_id)
        REFERENCES asientos_contables(id),

    CONSTRAINT ck_movimientos_caja_fecha_iso
        CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),

    CONSTRAINT ck_movimientos_caja_fecha_mes_dia
        CHECK (
            CAST(substr(fecha, 6, 2) AS INTEGER) BETWEEN 1 AND 12
            AND CAST(substr(fecha, 9, 2) AS INTEGER) BETWEEN 1 AND 31
        ),

    CONSTRAINT ck_movimientos_caja_tipo_movimiento
        CHECK (tipo_movimiento IN ('INGRESO', 'EGRESO')),

    CONSTRAINT ck_movimientos_caja_origen_completo
        CHECK (
            (origen_tipo IS NULL AND origen_id IS NULL)
            OR
            (origen_tipo IS NOT NULL AND origen_id IS NOT NULL)
        ),

    CONSTRAINT ck_movimientos_caja_origen_tipo_no_vacio
        CHECK (origen_tipo IS NULL OR length(trim(origen_tipo)) > 0),

    CONSTRAINT ck_movimientos_caja_origen_id_positivo
        CHECK (origen_id IS NULL OR origen_id > 0),

    CONSTRAINT ck_movimientos_caja_moneda_contable
        CHECK (moneda_contable_codigo GLOB '[A-Z][A-Z][A-Z]'),

    CONSTRAINT ck_movimientos_caja_total
        CHECK (
            typeof(total_contable_centavos) = 'integer'
            AND total_contable_centavos >= 0
        ),

    CONSTRAINT ck_movimientos_caja_estado
        CHECK (estado IN ('BORRADOR', 'CONFIRMADO', 'ANULADO')),

    CONSTRAINT ck_movimientos_caja_observaciones_no_vacias
        CHECK (observaciones IS NULL OR length(trim(observaciones)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_fecha
ON movimientos_caja (fecha, id);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_estado_fecha
ON movimientos_caja (estado, fecha, id);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_origen
ON movimientos_caja (origen_tipo, origen_id);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_asiento
ON movimientos_caja (asiento_id);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_moneda
ON movimientos_caja (moneda_contable_codigo);

CREATE TABLE IF NOT EXISTS movimientos_caja_lineas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movimiento_caja_id INTEGER NOT NULL,
    medio_operativo_codigo TEXT NOT NULL,
    cuenta_contable_codigo TEXT NOT NULL,
    moneda_codigo TEXT NOT NULL,
    fecha_valor TEXT,
    referencia TEXT,
    importe_nominal_centavos INTEGER NOT NULL,
    cotizacion_1000000 INTEGER NOT NULL DEFAULT 1000000,
    importe_contable_centavos INTEGER NOT NULL,
    detalle TEXT,
    orden INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT fk_movimientos_caja_lineas_movimiento
        FOREIGN KEY (movimiento_caja_id)
        REFERENCES movimientos_caja(id),

    CONSTRAINT fk_movimientos_caja_lineas_medio
        FOREIGN KEY (medio_operativo_codigo)
        REFERENCES medios_operativos(codigo),

    CONSTRAINT fk_movimientos_caja_lineas_cuenta
        FOREIGN KEY (cuenta_contable_codigo)
        REFERENCES cuentas_contables(cuenta),

    CONSTRAINT fk_movimientos_caja_lineas_moneda
        FOREIGN KEY (moneda_codigo)
        REFERENCES monedas(codigo),

    CONSTRAINT ck_movimientos_caja_lineas_medio_no_vacio
        CHECK (length(trim(medio_operativo_codigo)) > 0),

    CONSTRAINT ck_movimientos_caja_lineas_fecha_valor_iso
        CHECK (
            fecha_valor IS NULL
            OR fecha_valor GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        ),

    CONSTRAINT ck_movimientos_caja_lineas_fecha_valor_mes_dia
        CHECK (
            fecha_valor IS NULL
            OR (
                CAST(substr(fecha_valor, 6, 2) AS INTEGER) BETWEEN 1 AND 12
                AND CAST(substr(fecha_valor, 9, 2) AS INTEGER) BETWEEN 1 AND 31
            )
        ),

    CONSTRAINT ck_movimientos_caja_lineas_referencia_no_vacia
        CHECK (referencia IS NULL OR length(trim(referencia)) > 0),

    CONSTRAINT ck_movimientos_caja_lineas_moneda_codigo
        CHECK (moneda_codigo GLOB '[A-Z][A-Z][A-Z]'),

    CONSTRAINT ck_movimientos_caja_lineas_nominal
        CHECK (
            typeof(importe_nominal_centavos) = 'integer'
            AND importe_nominal_centavos > 0
        ),

    CONSTRAINT ck_movimientos_caja_lineas_cotizacion
        CHECK (
            typeof(cotizacion_1000000) = 'integer'
            AND cotizacion_1000000 > 0
        ),

    CONSTRAINT ck_movimientos_caja_lineas_contable
        CHECK (
            typeof(importe_contable_centavos) = 'integer'
            AND importe_contable_centavos > 0
        ),

    CONSTRAINT ck_movimientos_caja_lineas_detalle_no_vacio
        CHECK (detalle IS NULL OR length(trim(detalle)) > 0),

    CONSTRAINT ck_movimientos_caja_lineas_orden
        CHECK (typeof(orden) = 'integer' AND orden >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_movimientos_caja_lineas_orden
ON movimientos_caja_lineas (movimiento_caja_id, orden);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_lineas_movimiento
ON movimientos_caja_lineas (movimiento_caja_id, id);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_lineas_medio
ON movimientos_caja_lineas (medio_operativo_codigo);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_lineas_cuenta
ON movimientos_caja_lineas (cuenta_contable_codigo);

CREATE INDEX IF NOT EXISTS ix_movimientos_caja_lineas_moneda
ON movimientos_caja_lineas (moneda_codigo);
