CREATE TABLE IF NOT EXISTS caja_intenciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origen_tipo TEXT NOT NULL,
    origen_payload_json TEXT NOT NULL,
    tipo_movimiento TEXT NOT NULL,
    total_esperado_centavos INTEGER NOT NULL,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE',
    resultado_tipo TEXT,
    resultado_id INTEGER,
    observaciones TEXT,
    creado_en TEXT NOT NULL,
    confirmado_en TEXT,
    anulado_en TEXT,

    CONSTRAINT ck_caja_intenciones_origen_tipo_no_vacio
        CHECK (length(trim(origen_tipo)) > 0),

    CONSTRAINT ck_caja_intenciones_payload_no_vacio
        CHECK (length(trim(origen_payload_json)) > 0),

    CONSTRAINT ck_caja_intenciones_tipo_movimiento
        CHECK (tipo_movimiento IN ('INGRESO', 'EGRESO')),

    CONSTRAINT ck_caja_intenciones_total
        CHECK (
            typeof(total_esperado_centavos) = 'integer'
            AND total_esperado_centavos > 0
        ),

    CONSTRAINT ck_caja_intenciones_estado
        CHECK (estado IN ('PENDIENTE', 'CONFIRMADA', 'ANULADA')),

    CONSTRAINT ck_caja_intenciones_resultado_completo
        CHECK (
            (resultado_tipo IS NULL AND resultado_id IS NULL)
            OR
            (resultado_tipo IS NOT NULL AND resultado_id IS NOT NULL)
        ),

    CONSTRAINT ck_caja_intenciones_resultado_tipo_no_vacio
        CHECK (resultado_tipo IS NULL OR length(trim(resultado_tipo)) > 0),

    CONSTRAINT ck_caja_intenciones_resultado_id
        CHECK (resultado_id IS NULL OR resultado_id > 0),

    CONSTRAINT ck_caja_intenciones_observaciones_no_vacias
        CHECK (observaciones IS NULL OR length(trim(observaciones)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_caja_intenciones_estado
ON caja_intenciones (estado, creado_en, id);

CREATE INDEX IF NOT EXISTS ix_caja_intenciones_origen
ON caja_intenciones (origen_tipo, estado, id);

CREATE INDEX IF NOT EXISTS ix_caja_intenciones_resultado
ON caja_intenciones (resultado_tipo, resultado_id);
