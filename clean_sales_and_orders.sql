-- ============================================
-- Script para limpiar ventas y pedidos
-- Úsalo para empezar con datos limpios de prueba
-- ============================================
-- ADVERTENCIA: Este script eliminará TODAS las ventas, 
-- pedidos, pagos y registros relacionados.
-- ============================================

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

-- 5. Limpiar items de ventas (detalles)
DELETE FROM sale_items;

-- 6. Limpiar ventas (sales)
DELETE FROM sales;

-- 7. Limpiar pedidos
DELETE FROM pedidos;

-- 8. Limpiar productos de pedido
DELETE FROM productos_pedido;

-- 9. Limpiar movimientos de inventario (opcional, descomenta si quieres limpiar)
-- DELETE FROM inventory_movements;

-- 10. Limpiar turnos/shifts (opcional, descomenta si quieres limpiar)
-- DELETE FROM shifts;

-- Rehabilitar las restricciones de foreign keys
SET session_replication_role = 'origin';

-- Resetear secuencias (autoincrement) para empezar desde 1
ALTER SEQUENCE IF EXISTS sales_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS sale_items_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS pedidos_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS productos_pedido_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS pagos_pedido_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS credit_payments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS payments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS status_history_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS inventory_movements_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS shifts_id_seq RESTART WITH 1;

-- Mostrar resumen
SELECT 
    'Limpieza completada' as mensaje,
    (SELECT COUNT(*) FROM sales) as ventas_restantes,
    (SELECT COUNT(*) FROM pedidos) as pedidos_restantes,
    (SELECT COUNT(*) FROM productos_pedido) as productos_pedido_restantes,
    (SELECT COUNT(*) FROM pagos_pedido) as pagos_pedido_restantes,
    (SELECT COUNT(*) FROM credit_payments) as credit_payments_restantes,
    (SELECT COUNT(*) FROM payments) as payments_restantes;

-- ============================================
-- Los siguientes datos NO se eliminan:
-- - Usuarios (users)
-- - Productos del inventario (products)
-- - Clientes (clients)
-- - Tasas de metal (tasas_metal, tasas_metal_pedido)
-- - Configuraciones del sistema
-- ============================================

