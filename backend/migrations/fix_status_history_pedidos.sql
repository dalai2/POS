-- ============================================
-- CORREGIR HISTORIAL DE ESTADOS DE PEDIDOS
-- Eliminar registros huérfanos después de renumeración
-- ============================================

ROLLBACK;

BEGIN;

-- 1. Mostrar estado actual
SELECT 'Historial de estados ANTES de limpiar:' as info;
SELECT 
    sh.id,
    sh.entity_id,
    sh.old_status,
    sh.new_status,
    sh.user_email,
    sh.created_at,
    CASE WHEN p.id IS NULL THEN '❌ HUÉRFANO' ELSE '✅ OK' END as estado
FROM status_history sh
LEFT JOIN pedidos p ON sh.entity_id = p.id
WHERE sh.entity_type = 'pedido'
ORDER BY sh.entity_id, sh.created_at;

-- 2. Contar registros huérfanos
SELECT 'Conteo de registros huérfanos:' as info;
SELECT COUNT(*) as total_huerfanos
FROM status_history sh
LEFT JOIN pedidos p ON sh.entity_id = p.id
WHERE sh.entity_type = 'pedido' AND p.id IS NULL;

-- 3. Eliminar registros huérfanos (que apuntan a pedidos que ya no existen)
DELETE FROM status_history sh
WHERE sh.entity_type = 'pedido'
AND NOT EXISTS (
    SELECT 1 FROM pedidos p WHERE p.id = sh.entity_id
);

-- 4. Mostrar estado después de limpiar
SELECT 'Historial de estados DESPUÉS de limpiar:' as info;
SELECT 
    sh.id,
    sh.entity_id as pedido_id,
    p.folio_pedido,
    p.cliente_nombre,
    sh.old_status,
    sh.new_status,
    sh.user_email,
    sh.created_at
FROM status_history sh
JOIN pedidos p ON sh.entity_id = p.id
WHERE sh.entity_type = 'pedido'
ORDER BY sh.entity_id, sh.created_at;

COMMIT;

SELECT '✅ Historial de estados corregido' as resultado;

