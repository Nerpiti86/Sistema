ALTER TABLE ventas_comprobantes_detalle
ADD COLUMN unidad_medida_codigo TEXT NOT NULL DEFAULT '7';

ALTER TABLE ventas_comprobantes_detalle
ADD COLUMN tipo_bonificacion_codigo TEXT;

ALTER TABLE ventas_comprobantes_detalle
ADD COLUMN bonificacion_valor_10000 INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS ix_ventas_detalle_unidad_medida
ON ventas_comprobantes_detalle (unidad_medida_codigo);

CREATE INDEX IF NOT EXISTS ix_ventas_detalle_tipo_bonificacion
ON ventas_comprobantes_detalle (tipo_bonificacion_codigo);
