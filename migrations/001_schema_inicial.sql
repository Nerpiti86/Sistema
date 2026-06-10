CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT NOT NULL UNIQUE,
    valor TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

INSERT OR IGNORE INTO app_settings (clave, valor, created_at)
VALUES ('schema_version', '001', '1970-01-01 00:00:00');
