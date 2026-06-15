ALTER TABLE ventas_comprobantes
ADD COLUMN tipo_comprobante_codigo TEXT;

UPDATE ventas_comprobantes
SET tipo_comprobante_codigo = CASE tipo_comprobante
    WHEN 'FACTURA' THEN '011'
    WHEN 'NOTA_DEBITO' THEN '012'
    WHEN 'NOTA_CREDITO' THEN '013'
    ELSE tipo_comprobante_codigo
END
WHERE tipo_comprobante_codigo IS NULL;

CREATE INDEX IF NOT EXISTS ix_ventas_comprobantes_tipo_comprobante_codigo
ON ventas_comprobantes (tipo_comprobante_codigo);
