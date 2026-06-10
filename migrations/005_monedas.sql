CREATE TABLE IF NOT EXISTS monedas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    simbolo TEXT NOT NULL,
    decimales INTEGER NOT NULL DEFAULT 2,
    activa INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (codigo GLOB '[A-Z][A-Z][A-Z]'),
    CHECK (length(trim(nombre)) > 0),
    CHECK (length(trim(simbolo)) > 0),
    CHECK (decimales BETWEEN 0 AND 6),
    CHECK (activa IN (0, 1)),
    CHECK (orden >= 0)
);

CREATE INDEX IF NOT EXISTS ix_monedas_activa_orden
ON monedas (activa, orden, codigo);

INSERT OR IGNORE INTO monedas (
    codigo,
    nombre,
    simbolo,
    decimales,
    activa,
    orden,
    creado_en
)
VALUES
    ('ARS', 'Peso argentino', '$', 2, 1, 10, '1970-01-01 00:00:00'),
    ('USD', 'Dolar estadounidense', 'US$', 2, 1, 20, '1970-01-01 00:00:00'),
    ('EUR', 'Euro', '€', 2, 1, 30, '1970-01-01 00:00:00');
