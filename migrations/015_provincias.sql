CREATE TABLE IF NOT EXISTS provincias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pais_id INTEGER NOT NULL,
    nombre TEXT NOT NULL COLLATE NOCASE,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (length(trim(nombre)) > 0),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0),
    UNIQUE(pais_id, nombre),
    FOREIGN KEY (pais_id) REFERENCES paises(id)
);

CREATE INDEX IF NOT EXISTS ix_provincias_pais_activo_orden
ON provincias (pais_id, activo, orden, nombre);
