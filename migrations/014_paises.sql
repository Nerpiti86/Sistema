CREATE TABLE IF NOT EXISTS paises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL COLLATE NOCASE,
    codigo_iso TEXT COLLATE NOCASE,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (length(trim(nombre)) > 0),
    CHECK (codigo_iso IS NULL OR length(trim(codigo_iso)) IN (2, 3)),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0),
    UNIQUE(nombre),
    UNIQUE(codigo_iso)
);

CREATE INDEX IF NOT EXISTS ix_paises_activo_orden
ON paises (activo, orden, nombre);
