-- Verificar estado actual del contador de folios de ventas
SELECT '=== ESTADO ACTUAL DEL CONTADOR DE VENTAS ===' as seccion;
SELECT
    tenant_id,
    tipo,
    next_seq as siguiente_numero,
    'La próxima venta será V-' || LPAD(next_seq::text, 6, '0') as proxima_venta
FROM folio_counters
WHERE tipo = 'VENTA';

-- Verificar ventas existentes
SELECT '=== VENTAS EXISTENTES ===' as seccion;
SELECT
    id,
    folio_venta,
    customer_name as cliente,
    total,
    created_at
FROM ventas_contado
ORDER BY created_at ASC;
