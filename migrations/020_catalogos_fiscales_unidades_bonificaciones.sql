CREATE TABLE IF NOT EXISTS unidades_medida (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (length(trim(codigo)) > 0),
    CHECK (codigo NOT GLOB '*[^0-9]*'),
    CHECK (length(trim(descripcion)) > 0),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0)
);

CREATE INDEX IF NOT EXISTS ix_unidades_medida_activo_orden
ON unidades_medida (activo, orden, CAST(codigo AS INTEGER));

INSERT OR IGNORE INTO unidades_medida (
    codigo,
    descripcion,
    activo,
    orden,
    creado_en
)
VALUES
    ('1', 'kilogramos', 1, 10, '1970-01-01 00:00:00'),
    ('2', 'metros', 1, 20, '1970-01-01 00:00:00'),
    ('3', 'metros cuadrados', 1, 30, '1970-01-01 00:00:00'),
    ('4', 'metros cúbicos', 1, 40, '1970-01-01 00:00:00'),
    ('5', 'litros', 1, 50, '1970-01-01 00:00:00'),
    ('7', 'unidades', 1, 60, '1970-01-01 00:00:00'),
    ('14', 'gramos', 1, 70, '1970-01-01 00:00:00'),
    ('47', 'mililitros', 1, 80, '1970-01-01 00:00:00');

CREATE TABLE IF NOT EXISTS tipos_bonificacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (length(trim(codigo)) > 0),
    CHECK (codigo NOT GLOB '*[^0-9]*'),
    CHECK (length(trim(descripcion)) > 0),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0)
);

CREATE INDEX IF NOT EXISTS ix_tipos_bonificacion_activo_orden
ON tipos_bonificacion (activo, orden, CAST(codigo AS INTEGER));

INSERT OR IGNORE INTO tipos_bonificacion (
    codigo,
    descripcion,
    activo,
    orden,
    creado_en
)
VALUES
    ('1', 'Porcentaje', 1, 10, '1970-01-01 00:00:00'),
    ('2', 'Monto', 1, 20, '1970-01-01 00:00:00');
