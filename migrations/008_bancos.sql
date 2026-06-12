CREATE TABLE IF NOT EXISTS bancos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (codigo GLOB '[0-9A-Z][0-9A-Z][0-9A-Z][0-9A-Z][0-9A-Z]'),
    CHECK (length(trim(nombre)) > 0),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0)
);

CREATE INDEX IF NOT EXISTS ix_bancos_activo_orden
ON bancos (activo, orden, codigo);
