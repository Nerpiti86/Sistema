CREATE TABLE IF NOT EXISTS ejercicios_contables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    fecha_desde TEXT NOT NULL,
    fecha_hasta TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ABIERTO',
    activo INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,
    fase_cierre TEXT NOT NULL DEFAULT 'ABIERTO',
    bloqueado INTEGER NOT NULL DEFAULT 0,
    bloqueado_en TEXT,
    observaciones_cierre TEXT,
    es_primer_ejercicio INTEGER NOT NULL DEFAULT 0,

    CHECK (length(trim(codigo)) > 0),
    CHECK (length(trim(nombre)) > 0),
    CHECK (fecha_desde GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    CHECK (fecha_hasta GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    CHECK (fecha_hasta >= fecha_desde),
    CHECK (estado IN ('ABIERTO', 'CERRADO')),
    CHECK (activo IN (0, 1)),
    CHECK (fase_cierre IN ('ABIERTO', 'EN_CIERRE', 'BLOQUEADO')),
    CHECK (bloqueado IN (0, 1)),
    CHECK (es_primer_ejercicio IN (0, 1))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ejercicios_contables_activo_unico
ON ejercicios_contables (activo)
WHERE activo = 1;

CREATE INDEX IF NOT EXISTS ix_ejercicios_contables_fechas
ON ejercicios_contables (fecha_desde, fecha_hasta);

CREATE INDEX IF NOT EXISTS ix_ejercicios_contables_estado
ON ejercicios_contables (estado, fase_cierre, bloqueado);
