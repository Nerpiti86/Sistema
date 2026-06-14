CREATE TABLE IF NOT EXISTS grupos_clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL COLLATE NOCASE,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (length(trim(nombre)) > 0),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0),
    UNIQUE(nombre)
);

CREATE INDEX IF NOT EXISTS ix_grupos_clientes_activo_orden
ON grupos_clientes (activo, orden, nombre);
