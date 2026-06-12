CREATE TABLE IF NOT EXISTS bancos_contrato_final (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (
        (
            length(trim(codigo)) BETWEEN 1 AND 5
            AND codigo NOT GLOB '*[^0-9]*'
        )
        OR (
            length(trim(codigo)) = 5
            AND codigo GLOB '[0-9A-Z][0-9A-Z][0-9A-Z][0-9A-Z][0-9A-Z]'
        )
    ),
    CHECK (length(trim(nombre)) > 0),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0)
);

INSERT INTO bancos_contrato_final (
    id,
    codigo,
    nombre,
    activo,
    orden,
    creado_en,
    actualizado_en
)
SELECT
    id,
    codigo,
    nombre,
    activo,
    orden,
    creado_en,
    actualizado_en
FROM bancos
WHERE (
        length(trim(codigo)) BETWEEN 1 AND 5
        AND codigo NOT GLOB '*[^0-9]*'
    )
    OR (
        length(trim(codigo)) = 5
        AND codigo GLOB '[0-9A-Z][0-9A-Z][0-9A-Z][0-9A-Z][0-9A-Z]'
    );

DROP TABLE bancos;
ALTER TABLE bancos_contrato_final RENAME TO bancos;

CREATE INDEX IF NOT EXISTS ix_bancos_activo_orden
ON bancos (activo, orden, codigo);
