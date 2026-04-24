-- ============================================
-- RESETEAR CONTADOR DE FOLIOS DE VENTAS
-- Sin modificar la información existente
-- ============================================

-- Verificar estado actual del contador de ventas
SELECT '=== CONTADOR ACTUAL DE VENTAS ===' as seccion;
SELECT
    tenant_id,
    tipo,
    next_seq as siguiente_numero
FROM folio_counters
WHERE tipo = 'VENTA';

-- Resetear el contador de ventas a 1
UPDATE folio_counters
SET next_seq = 1
WHERE tipo = 'VENTA';

-- Verificar que se reseteó correctamente
SELECT '=== CONTADOR DE VENTAS DESPUÉS DEL RESET ===' as seccion;
SELECT
    tenant_id,
    tipo,
    next_seq as siguiente_numero
FROM folio_counters
WHERE tipo = 'VENTA';

-- Mostrar confirmación
SELECT
    'Contador de folios de ventas reseteado exitosamente' as mensaje,
    'La próxima venta tendrá folio V-000001' as nota;
