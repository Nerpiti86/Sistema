CREATE TABLE IF NOT EXISTS indices_inflacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    periodo_yyyymm INTEGER NOT NULL UNIQUE,
    indice_10000 INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TEXT,

    CHECK (periodo_yyyymm BETWEEN 190001 AND 299912),
    CHECK ((periodo_yyyymm % 100) BETWEEN 1 AND 12),
    CHECK (indice_10000 > 0)
);

CREATE TABLE IF NOT EXISTS ejercicios_coeficientes_inflacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejercicio_id INTEGER NOT NULL,
    periodo_yyyymm INTEGER NOT NULL,
    indice_inicio_10000 INTEGER NOT NULL,
    indice_cierre_periodo_yyyymm INTEGER NOT NULL,
    indice_cierre_10000 INTEGER NOT NULL,
    coeficiente_1000000000000 INTEGER NOT NULL,
    calculado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ejercicio_id)
        REFERENCES ejercicios_contables (id)
        ON DELETE CASCADE,

    UNIQUE (ejercicio_id, periodo_yyyymm),

    CHECK (periodo_yyyymm BETWEEN 190001 AND 299912),
    CHECK ((periodo_yyyymm % 100) BETWEEN 1 AND 12),
    CHECK (indice_cierre_periodo_yyyymm BETWEEN 190001 AND 299912),
    CHECK ((indice_cierre_periodo_yyyymm % 100) BETWEEN 1 AND 12),
    CHECK (indice_inicio_10000 > 0),
    CHECK (indice_cierre_10000 > 0),
    CHECK (coeficiente_1000000000000 > 0)
);

CREATE INDEX IF NOT EXISTS ix_indices_inflacion_periodo
ON indices_inflacion (periodo_yyyymm);

CREATE INDEX IF NOT EXISTS ix_ec_coef_inflacion_ejercicio
ON ejercicios_coeficientes_inflacion (ejercicio_id);

CREATE INDEX IF NOT EXISTS ix_ec_coef_inflacion_periodo
ON ejercicios_coeficientes_inflacion (periodo_yyyymm);
