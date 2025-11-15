-- Script para borrar todas las ventas y resetear secuencias
-- ADVERTENCIA: Esta operación es destructiva y no se puede deshacer

ROLLBACK;  -- Limpiar cualquier transacción abortada
BEGIN;

-- 1. Borrar tickets relacionados a ventas
DELETE FROM tickets WHERE kind IN ('sale', 'payment');

-- 2. Borrar historial de estados de ventas
DELETE FROM status_history WHERE entity_type = 'sale';

-- 3. Borrar pagos de crédito (abonos)
DELETE FROM credit_payments;

-- 4. Borrar pagos iniciales de apartados
DELETE FROM payments;

-- 5. Borrar items de ventas
DELETE FROM sale_items;

-- 6. Borrar ventas
DELETE FROM sales;

-- 7. Resetear secuencias
ALTER SEQUENCE sales_id_seq RESTART WITH 1;
ALTER SEQUENCE sale_items_id_seq RESTART WITH 1;
ALTER SEQUENCE payments_id_seq RESTART WITH 1;
ALTER SEQUENCE credit_payments_id_seq RESTART WITH 1;

COMMIT;

-- Verificar resultados
SELECT 'Ventas borradas. Verificación:' as info;
SELECT 'Sales' as tabla, COUNT(*) as registros FROM sales
UNION ALL
SELECT 'Sale Items' as tabla, COUNT(*) as registros FROM sale_items
UNION ALL
SELECT 'Payments' as tabla, COUNT(*) as registros FROM payments
UNION ALL
SELECT 'Credit Payments' as tabla, COUNT(*) as registros FROM credit_payments
UNION ALL
SELECT 'Status History (sales)' as tabla, COUNT(*) as registros FROM status_history WHERE entity_type = 'sale'
UNION ALL
SELECT 'Tickets (sales)' as tabla, COUNT(*) as registros FROM tickets WHERE kind IN ('sale', 'payment');
