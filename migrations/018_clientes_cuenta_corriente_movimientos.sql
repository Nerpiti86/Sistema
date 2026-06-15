CREATE TABLE IF NOT EXISTS clientes_cuenta_corriente_movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    tipo_movimiento TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    moneda_codigo TEXT NOT NULL DEFAULT 'ARS',
    debe_centavos INTEGER NOT NULL DEFAULT 0,
    haber_centavos INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'BORRADOR',
    origen_tipo TEXT,
    origen_id INTEGER,
    asiento_id INTEGER,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,
    confirmado_en TEXT,
    anulado_en TEXT,

    CONSTRAINT fk_clientes_ctacte_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id),

    CONSTRAINT fk_clientes_ctacte_moneda
        FOREIGN KEY (moneda_codigo)
        REFERENCES monedas(codigo),

    CONSTRAINT fk_clientes_ctacte_asiento
        FOREIGN KEY (asiento_id)
        REFERENCES asientos_contables(id),

    CONSTRAINT ck_clientes_ctacte_fecha_iso
        CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),

    CONSTRAINT ck_clientes_ctacte_fecha_mes_dia
        CHECK (
            CAST(substr(fecha, 6, 2) AS INTEGER) BETWEEN 1 AND 12
            AND CAST(substr(fecha, 9, 2) AS INTEGER) BETWEEN 1 AND 31
        ),

    CONSTRAINT ck_clientes_ctacte_tipo_movimiento
        CHECK (
            tipo_movimiento IN (
                'FACTURA',
                'NOTA_DEBITO',
                'NOTA_CREDITO',
                'COBRANZA',
                'ANTICIPO',
                'AJUSTE'
            )
        ),

    CONSTRAINT ck_clientes_ctacte_descripcion_no_vacia
        CHECK (length(trim(descripcion)) > 0),

    CONSTRAINT ck_clientes_ctacte_moneda_codigo
        CHECK (moneda_codigo GLOB '[A-Z][A-Z][A-Z]'),

    CONSTRAINT ck_clientes_ctacte_debe_entero_no_negativo
        CHECK (
            typeof(debe_centavos) = 'integer'
            AND debe_centavos >= 0
        ),

    CONSTRAINT ck_clientes_ctacte_haber_entero_no_negativo
        CHECK (
            typeof(haber_centavos) = 'integer'
            AND haber_centavos >= 0
        ),

    CONSTRAINT ck_clientes_ctacte_un_solo_lado
        CHECK (
            (debe_centavos > 0 AND haber_centavos = 0)
            OR
            (debe_centavos = 0 AND haber_centavos > 0)
        ),

    CONSTRAINT ck_clientes_ctacte_estado
        CHECK (estado IN ('BORRADOR', 'CONFIRMADO', 'ANULADO')),

    CONSTRAINT ck_clientes_ctacte_origen_completo
        CHECK (
            (origen_tipo IS NULL AND origen_id IS NULL)
            OR
            (origen_tipo IS NOT NULL AND origen_id IS NOT NULL)
        ),

    CONSTRAINT ck_clientes_ctacte_origen_tipo_no_vacio
        CHECK (origen_tipo IS NULL OR length(trim(origen_tipo)) > 0),

    CONSTRAINT ck_clientes_ctacte_origen_id_positivo
        CHECK (origen_id IS NULL OR origen_id > 0)
);

CREATE INDEX IF NOT EXISTS ix_clientes_ctacte_cliente_fecha
ON clientes_cuenta_corriente_movimientos (cliente_id, fecha, id);

CREATE INDEX IF NOT EXISTS ix_clientes_ctacte_cliente_estado
ON clientes_cuenta_corriente_movimientos (cliente_id, estado, fecha, id);

CREATE INDEX IF NOT EXISTS ix_clientes_ctacte_origen
ON clientes_cuenta_corriente_movimientos (origen_tipo, origen_id);

CREATE INDEX IF NOT EXISTS ix_clientes_ctacte_asiento
ON clientes_cuenta_corriente_movimientos (asiento_id);

CREATE INDEX IF NOT EXISTS ix_clientes_ctacte_moneda
ON clientes_cuenta_corriente_movimientos (moneda_codigo);
