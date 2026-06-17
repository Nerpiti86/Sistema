CREATE UNIQUE INDEX IF NOT EXISTS ux_movimientos_caja_origen_unico
ON movimientos_caja (origen_tipo, origen_id)
WHERE origen_tipo IS NOT NULL
  AND origen_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_cobranzas_asiento
ON clientes_cobranzas (asiento_id)
WHERE asiento_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_movimientos_caja_asiento
ON movimientos_caja (asiento_id)
WHERE asiento_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_cobranzas_lineas_ctacte_generada
ON clientes_cobranzas_lineas (movimiento_ctacte_generado_id)
WHERE movimiento_ctacte_generado_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_cobranzas_lineas_cobranza_ctacte_cancelada
ON clientes_cobranzas_lineas (cobranza_cliente_id, movimiento_ctacte_cancelado_id)
WHERE movimiento_ctacte_cancelado_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_cobranzas_lineas_cobranza_comprobante
ON clientes_cobranzas_lineas (cobranza_cliente_id, venta_comprobante_id)
WHERE venta_comprobante_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_cobranzas_lineas_anticipo_unico
ON clientes_cobranzas_lineas (cobranza_cliente_id)
WHERE tipo_linea = 'ANTICIPO';
