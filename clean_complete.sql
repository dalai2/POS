-- Script COMPLETO para limpiar ventas, pedidos, apartados y clientes
-- Deshabilitar temporalmente las restricciones de foreign keys
SET session_replication_role = 'replica';

-- 1. Limpiar pagos de pedidos
DELETE FROM pagos_pedido;

-- 2. Limpiar pagos de crédito
DELETE FROM credit_payments;

-- 3. Limpiar pagos generales
DELETE FROM payments;

-- 4. Limpiar historial de estados
DELETE FROM status_history;

-- 5. Limpiar items de ventas al contado
DELETE FROM items_venta_contado;

-- 6. Limpiar ventas al contado
DELETE FROM ventas_contado;

-- 7. Limpiar items de apartados
DELETE FROM items_apartado;

-- 8. Limpiar apartados
DELETE FROM apartados;

-- 9. Limpiar items de pedidos
DELETE FROM pedido_items;

-- 10. Limpiar pedidos
DELETE FROM pedidos;

-- 11. Limpiar productos de pedido
DELETE FROM productos_pedido;

-- 12. Limpiar clientes registrados
DELETE FROM customers;

-- 13. Limpiar tickets
DELETE FROM tickets;

-- Rehabilitar las restricciones de foreign keys
SET session_replication_role = 'origin';

-- Resetear secuencias (autoincrement) para empezar desde 1
ALTER SEQUENCE IF EXISTS customers_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS ventas_contado_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS items_venta_contado_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS apartados_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS items_apartado_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS pedidos_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS pedido_items_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS productos_pedido_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS pagos_pedido_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS credit_payments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS payments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS status_history_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS tickets_id_seq RESTART WITH 1;

-- Mostrar resumen completo
SELECT
    'Limpieza COMPLETA realizada' as mensaje,
    (SELECT COUNT(*) FROM customers) as clientes_restantes,
    (SELECT COUNT(*) FROM ventas_contado) as ventas_contado_restantes,
    (SELECT COUNT(*) FROM apartados) as apartados_restantes,
    (SELECT COUNT(*) FROM pedidos) as pedidos_restantes,
    (SELECT COUNT(*) FROM productos_pedido) as productos_pedido_restantes,
    (SELECT COUNT(*) FROM pagos_pedido) as pagos_pedido_restantes,
    (SELECT COUNT(*) FROM credit_payments) as credit_payments_restantes,
    (SELECT COUNT(*) FROM payments) as payments_restantes,
    (SELECT COUNT(*) FROM tickets) as tickets_restantes;
