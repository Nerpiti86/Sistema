CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    razon_social TEXT NOT NULL COLLATE NOCASE,
    nombre_fantasia TEXT COLLATE NOCASE,
    grupo_cliente_id INTEGER NOT NULL,
    telefono TEXT,
    email TEXT COLLATE NOCASE,
    domicilio TEXT,
    codigo_postal TEXT,
    ciudad TEXT COLLATE NOCASE,
    pais_id INTEGER,
    provincia_id INTEGER,
    condicion_iva_codigo TEXT,
    tipo_documento_fiscal_codigo TEXT,
    numero_documento_fiscal TEXT,
    cuenta_deudores_ventas_codigo TEXT,
    cuenta_anticipo_clientes_codigo TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT,
    creado_en TEXT NOT NULL,
    actualizado_en TEXT,

    CHECK (length(trim(razon_social)) > 0),
    CHECK (nombre_fantasia IS NULL OR length(trim(nombre_fantasia)) > 0),
    CHECK (telefono IS NULL OR length(trim(telefono)) > 0),
    CHECK (email IS NULL OR length(trim(email)) > 0),
    CHECK (domicilio IS NULL OR length(trim(domicilio)) > 0),
    CHECK (codigo_postal IS NULL OR length(trim(codigo_postal)) > 0),
    CHECK (ciudad IS NULL OR length(trim(ciudad)) > 0),
    CHECK (numero_documento_fiscal IS NULL OR length(trim(numero_documento_fiscal)) > 0),
    CHECK (observaciones IS NULL OR length(trim(observaciones)) > 0),
    CHECK (
        (tipo_documento_fiscal_codigo IS NULL AND numero_documento_fiscal IS NULL)
        OR
        (tipo_documento_fiscal_codigo IS NOT NULL AND numero_documento_fiscal IS NOT NULL)
    ),
    CHECK (provincia_id IS NULL OR pais_id IS NOT NULL),
    CHECK (activo IN (0, 1)),
    CHECK (orden >= 0),

    FOREIGN KEY (grupo_cliente_id) REFERENCES grupos_clientes(id),
    FOREIGN KEY (pais_id) REFERENCES paises(id),
    FOREIGN KEY (provincia_id) REFERENCES provincias(id),
    FOREIGN KEY (condicion_iva_codigo) REFERENCES condiciones_iva(codigo),
    FOREIGN KEY (tipo_documento_fiscal_codigo) REFERENCES tipos_documento(codigo),
    FOREIGN KEY (cuenta_deudores_ventas_codigo) REFERENCES cuentas_contables(cuenta),
    FOREIGN KEY (cuenta_anticipo_clientes_codigo) REFERENCES cuentas_contables(cuenta)
);

CREATE INDEX IF NOT EXISTS ix_clientes_activo_razon_social
ON clientes (activo, razon_social);

CREATE INDEX IF NOT EXISTS ix_clientes_grupo_cliente
ON clientes (grupo_cliente_id, activo, razon_social);

CREATE INDEX IF NOT EXISTS ix_clientes_pais_provincia
ON clientes (pais_id, provincia_id, activo, razon_social);

CREATE INDEX IF NOT EXISTS ix_clientes_condicion_iva
ON clientes (condicion_iva_codigo);

CREATE INDEX IF NOT EXISTS ix_clientes_documento_fiscal
ON clientes (tipo_documento_fiscal_codigo, numero_documento_fiscal);

CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_documento_fiscal
ON clientes (tipo_documento_fiscal_codigo, numero_documento_fiscal)
WHERE tipo_documento_fiscal_codigo IS NOT NULL
  AND numero_documento_fiscal IS NOT NULL;
