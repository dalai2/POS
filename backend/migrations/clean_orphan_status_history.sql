-- ============================================
-- LIMPIAR HISTORIAL HUÉRFANO DE PEDIDOS
-- Eliminar registros de historial que son más viejos
-- que la fecha de creación del pedido actual
-- ============================================

ROLLBACK;

BEGIN;

-- 1. Ver registros problemáticos
SELECT '=== REGISTROS DE HISTORIAL HUÉRFANOS ===' as info;
SELECT 
    sh.id as history_id,
    sh.entity_id as pedido_id,
    sh.created_at as history_date,
    p.created_at as pedido_date,
    sh.notes,
    CASE 
        WHEN sh.created_at < p.created_at THEN '❌ HUÉRFANO (historial antes de creación del pedido)'
        ELSE '✅ OK'
    END as status
FROM status_history sh
JOIN pedidos p ON sh.entity_id = p.id
WHERE sh.entity_type = 'pedido'
AND sh.created_at < p.created_at
ORDER BY sh.entity_id, sh.created_at;

-- 2. Contar cuántos registros se van a eliminar
SELECT '=== TOTAL A ELIMINAR ===' as info;
SELECT COUNT(*) as total_a_eliminar
FROM status_history sh
JOIN pedidos p ON sh.entity_id = p.id
WHERE sh.entity_type = 'pedido'
AND sh.created_at < p.created_at;

-- 3. Eliminar registros huérfanos (historial más viejo que el pedido)
DELETE FROM status_history sh
USING pedidos p
WHERE sh.entity_id = p.id
AND sh.entity_type = 'pedido'
AND sh.created_at < p.created_at;

-- 4. Verificar resultado
SELECT '=== HISTORIAL DESPUÉS DE LIMPIAR ===' as info;
SELECT 
    sh.id as history_id,
    sh.entity_id as pedido_id,
    p.folio_pedido,
    p.cliente_nombre,
    sh.old_status,
    sh.new_status,
    sh.notes,
    sh.created_at as history_date,
    p.created_at as pedido_date
FROM status_history sh
JOIN pedidos p ON sh.entity_id = p.id
WHERE sh.entity_type = 'pedido'
ORDER BY sh.entity_id, sh.created_at;

COMMIT;

SELECT '✅ Historial huérfano eliminado correctamente' as resultado;

