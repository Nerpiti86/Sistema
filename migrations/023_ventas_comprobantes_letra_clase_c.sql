UPDATE ventas_comprobantes
SET letra = 'C'
WHERE tipo_comprobante_codigo IN ('011', '012', '013')
  AND letra != 'C';
