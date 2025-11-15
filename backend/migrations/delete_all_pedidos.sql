-- Script para borrar todos los pedidos y resetear secuencias
-- ADVERTENCIA: Esta operación es destructiva y no se puede deshacer

ROLLBACK;  -- Limpiar cualquier transacción abortada
BEGIN;

-- 1. Borrar tickets relacionados a pedidos
DELETE FROM tickets WHERE kind LIKE 'pedido%' OR kind = 'payment';

-- 2. Borrar historial de estados de pedidos
DELETE FROM status_history WHERE entity_type = 'pedido';

-- 3. Borrar pagos de pedidos (abonos y anticipos)
DELETE FROM pagos_pedido;

-- 4. Borrar items de pedidos
DELETE FROM pedido_items;

-- 5. Borrar pedidos
DELETE FROM pedidos;

-- 6. Resetear secuencias
ALTER SEQUENCE pedidos_id_seq RESTART WITH 1;
ALTER SEQUENCE pedido_items_id_seq RESTART WITH 1;
ALTER SEQUENCE pagos_pedido_id_seq RESTART WITH 1;

COMMIT;

-- Verificar resultados
SELECT 'Pedidos borrados. Verificación:' as info;
SELECT 'Pedidos' as tabla, COUNT(*) as registros FROM pedidos
UNION ALL
SELECT 'Pedido Items' as tabla, COUNT(*) as registros FROM pedido_items
UNION ALL
SELECT 'Pagos Pedido' as tabla, COUNT(*) as registros FROM pagos_pedido
UNION ALL
SELECT 'Status History (pedidos)' as tabla, COUNT(*) as registros FROM status_history WHERE entity_type = 'pedido'
UNION ALL
SELECT 'Tickets (pedidos)' as tabla, COUNT(*) as registros FROM tickets WHERE kind LIKE 'pedido%';
