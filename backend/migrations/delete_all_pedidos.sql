-- ============================================
-- BORRAR TODOS LOS PEDIDOS Y DATOS RELACIONADOS
-- ============================================

ROLLBACK;

BEGIN;

-- 1. Mostrar lo que se va a borrar
SELECT '=== PEDIDOS A BORRAR ===' as info;
SELECT COUNT(*) as total_pedidos FROM pedidos;
SELECT id, folio_pedido, cliente_nombre, total FROM pedidos ORDER BY id;

SELECT '=== PAGOS DE PEDIDOS A BORRAR ===' as info;
SELECT COUNT(*) as total_pagos FROM pagos_pedido;

SELECT '=== ITEMS DE PEDIDOS A BORRAR ===' as info;
SELECT COUNT(*) as total_items FROM pedido_items;

SELECT '=== HISTORIAL DE PEDIDOS A BORRAR ===' as info;
SELECT COUNT(*) as total_historial FROM status_history WHERE entity_type = 'pedido';

SELECT '=== TICKETS DE PEDIDOS A BORRAR ===' as info;
SELECT COUNT(*) as total_tickets FROM tickets WHERE kind LIKE 'pedido%' OR kind = 'payment';

-- 2. Borrar tickets de pedidos
DELETE FROM tickets 
WHERE kind LIKE 'pedido%' OR kind = 'payment';

-- 3. Borrar historial de estados de pedidos
DELETE FROM status_history 
WHERE entity_type = 'pedido';

-- 4. Borrar pagos de pedidos
DELETE FROM pagos_pedido;

-- 5. Borrar items de pedidos
DELETE FROM pedido_items;

-- 6. Borrar todos los pedidos
DELETE FROM pedidos;

-- 7. Resetear la secuencia a 1
ALTER SEQUENCE pedidos_id_seq RESTART WITH 1;

-- 8. Verificar que todo está limpio
SELECT '=== DESPUÉS DEL BORRADO ===' as info;
SELECT COUNT(*) as pedidos_restantes FROM pedidos;
SELECT COUNT(*) as pagos_restantes FROM pagos_pedido;
SELECT COUNT(*) as items_restantes FROM pedido_items;
SELECT COUNT(*) as historial_restantes FROM status_history WHERE entity_type = 'pedido';
SELECT COUNT(*) as tickets_restantes FROM tickets WHERE kind LIKE 'pedido%' OR kind = 'payment';
SELECT last_value as proximo_id FROM pedidos_id_seq;

COMMIT;

SELECT '✅ Todos los pedidos han sido eliminados. El próximo pedido será ID 1' as resultado;

