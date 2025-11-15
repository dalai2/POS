-- ============================================
-- DEBUG: Ver estado de pedidos y su historial
-- ============================================

-- Ver todos los pedidos actuales
SELECT '=== PEDIDOS ACTUALES ===' as info;
SELECT id, folio_pedido, cliente_nombre, anticipo_pagado, created_at
FROM pedidos
ORDER BY id;

-- Ver todo el historial de estados de pedidos
SELECT '=== HISTORIAL DE ESTADOS ===' as info;
SELECT 
    sh.id as history_id,
    sh.entity_id as pedido_id,
    sh.old_status,
    sh.new_status,
    sh.notes,
    sh.created_at,
    sh.user_email
FROM status_history sh
WHERE sh.entity_type = 'pedido'
ORDER BY sh.entity_id, sh.created_at;

-- Ver relación entre pedidos y su historial
SELECT '=== RELACIÓN PEDIDO-HISTORIAL ===' as info;
SELECT 
    p.id as pedido_id,
    p.folio_pedido,
    p.cliente_nombre,
    COUNT(sh.id) as cantidad_historiales,
    string_agg(sh.notes, ' | ' ORDER BY sh.created_at) as notas
FROM pedidos p
LEFT JOIN status_history sh ON sh.entity_id = p.id AND sh.entity_type = 'pedido'
GROUP BY p.id, p.folio_pedido, p.cliente_nombre
ORDER BY p.id;

-- Ver detalles específicos del pedido que está causando problema
SELECT '=== DETALLE PEDIDO CON PROBLEMA ===' as info;
SELECT 
    p.id,
    p.folio_pedido,
    p.cliente_nombre,
    p.anticipo_pagado,
    p.created_at as pedido_created
FROM pedidos p
WHERE p.cliente_nombre LIKE '%Pedro%' OR p.cliente_nombre LIKE '%Ricardo%'
ORDER BY p.id;

-- Ver historial de ese pedido específico
SELECT '=== HISTORIAL DEL PEDIDO CON PROBLEMA ===' as info;
SELECT 
    sh.id,
    sh.entity_id,
    sh.notes,
    sh.created_at,
    p.folio_pedido,
    p.anticipo_pagado
FROM status_history sh
LEFT JOIN pedidos p ON p.id = sh.entity_id
WHERE sh.entity_type = 'pedido' 
AND (p.cliente_nombre LIKE '%Pedro%' OR p.cliente_nombre LIKE '%Ricardo%' OR sh.entity_id IN (1, 2))
ORDER BY sh.entity_id, sh.created_at;

