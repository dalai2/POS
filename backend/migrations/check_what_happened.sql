-- Ver qué quedó
SELECT '=== PEDIDOS ACTUALES ===' as info;
SELECT id, folio_pedido, cliente_nombre, anticipo_pagado, created_at, updated_at
FROM pedidos
ORDER BY id;

SELECT '=== HISTORIAL RESTANTE ===' as info;
SELECT 
    sh.id,
    sh.entity_id,
    sh.entity_type,
    sh.old_status,
    sh.new_status,
    sh.notes,
    sh.created_at,
    sh.user_email
FROM status_history sh
WHERE sh.entity_type = 'pedido'
ORDER BY sh.entity_id, sh.created_at;

SELECT '=== TODOS LOS HISTORIALES (incluyendo sales) ===' as info;
SELECT 
    id,
    entity_type,
    entity_id,
    notes,
    created_at
FROM status_history
ORDER BY entity_type, entity_id, created_at;

