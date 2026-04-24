-- ============================================
-- ACTUALIZAR FOLIOS DE VENTAS EXISTENTES Y CONTADOR
-- ============================================

-- 1. Verificar ventas actuales con sus folios
SELECT '=== VENTAS ACTUALES ===' as seccion;
SELECT
    id,
    folio_venta,
    customer_name as cliente,
    total,
    created_at
FROM ventas_contado
ORDER BY created_at ASC;

-- 2. Actualizar folios de las ventas existentes en orden de creación
WITH ventas_ordenadas AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at ASC) as num
    FROM ventas_contado
    ORDER BY created_at ASC
)
UPDATE ventas_contado v
SET folio_venta = 'V-' || LPAD(vo.num::text, 6, '0')
FROM ventas_ordenadas vo
WHERE v.id = vo.id;

-- 3. Actualizar el contador para que la próxima venta sea V-000006
UPDATE folio_counters
SET next_seq = 6
WHERE tipo = 'VENTA';

-- 4. Verificar ventas actualizadas
SELECT '=== VENTAS DESPUÉS DE ACTUALIZAR FOLIOS ===' as seccion;
SELECT
    id,
    folio_venta,
    customer_name as cliente,
    total,
    created_at
FROM ventas_contado
ORDER BY created_at ASC;

-- 5. Verificar contador actualizado
SELECT '=== CONTADOR DE FOLIOS ACTUALIZADO ===' as seccion;
SELECT
    tenant_id,
    tipo,
    next_seq as siguiente_numero,
    'La próxima venta será V-000006' as nota
FROM folio_counters
WHERE tipo = 'VENTA';
