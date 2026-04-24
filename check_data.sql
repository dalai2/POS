-- Verificación de datos actuales
SELECT '=== CLIENTES REGISTRADOS ===' as seccion;
SELECT COUNT(*) as total_clientes FROM customers;

SELECT '=== VENTAS AL CONTADO ===' as seccion;
SELECT COUNT(*) as total_ventas_contado, COALESCE(SUM(total), 0) as total_monto FROM ventas_contado;

SELECT '=== APARTADOS ===' as seccion;
SELECT COUNT(*) as total_apartados, COALESCE(SUM(total), 0) as total_monto FROM apartados;

SELECT '=== PEDIDOS ===' as seccion;
SELECT COUNT(*) as total_pedidos, COALESCE(SUM(total), 0) as total_monto FROM pedidos;

SELECT '=== PAGOS ===' as seccion;
SELECT 'Pagos generales' as tipo, COUNT(*) as cantidad FROM payments
UNION ALL
SELECT 'Pagos de crédito', COUNT(*) FROM credit_payments
UNION ALL
SELECT 'Pagos de pedidos', COUNT(*) FROM pagos_pedido;

SELECT '=== RESUMEN GENERAL ===' as seccion;
SELECT 'Clientes registrados' as tipo, COUNT(*) as cantidad FROM customers
UNION ALL
SELECT 'Ventas al contado', COUNT(*) FROM ventas_contado
UNION ALL
SELECT 'Apartados', COUNT(*) FROM apartados
UNION ALL
SELECT 'Pedidos', COUNT(*) FROM pedidos;
