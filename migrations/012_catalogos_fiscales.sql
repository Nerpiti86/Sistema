CREATE TABLE IF NOT EXISTS condiciones_iva (
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

CREATE INDEX IF NOT EXISTS ix_condiciones_iva_activo_orden
ON condiciones_iva (activo, orden, CAST(codigo AS INTEGER));

INSERT OR IGNORE INTO condiciones_iva (
    codigo,
    descripcion,
    activo,
    orden,
    creado_en
)
VALUES
    ('1', 'IVA Responsable No Inscripto', 1, 10, '1970-01-01 00:00:00'),
    ('4', 'IVA Sujeto Exento', 1, 20, '1970-01-01 00:00:00'),
    ('5', 'Consumidor Final', 1, 30, '1970-01-01 00:00:00'),
    ('6', 'Responsable Monotributo', 1, 40, '1970-01-01 00:00:00'),
    ('8', 'Proveedor del Exterior', 1, 50, '1970-01-01 00:00:00'),
    ('9', 'Cliente del Exterior', 1, 60, '1970-01-01 00:00:00'),
    ('10', 'IVA Liberado - Ley 19.640', 1, 70, '1970-01-01 00:00:00'),
    ('13', 'Monotributista Social', 1, 80, '1970-01-01 00:00:00'),
    ('15', 'IVA No Alcanzado', 1, 90, '1970-01-01 00:00:00');

CREATE TABLE IF NOT EXISTS tipos_documento (
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

CREATE INDEX IF NOT EXISTS ix_tipos_documento_activo_orden
ON tipos_documento (activo, orden, CAST(codigo AS INTEGER));

INSERT OR IGNORE INTO tipos_documento (
    codigo,
    descripcion,
    activo,
    orden,
    creado_en
)
VALUES
    ('80', 'CUIT', 1, 10, '1970-01-01 00:00:00'),
    ('87', 'CDI', 1, 20, '1970-01-01 00:00:00'),
    ('91', 'CI Extranjera', 1, 30, '1970-01-01 00:00:00'),
    ('94', 'Pasaporte', 1, 40, '1970-01-01 00:00:00'),
    ('96', 'DNI', 1, 50, '1970-01-01 00:00:00'),
    ('99', 'Otro', 1, 60, '1970-01-01 00:00:00');
