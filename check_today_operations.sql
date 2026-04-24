-- ============================================
-- REVISIÓN DE OPERACIONES DEL DÍA DE HOY
-- ============================================

-- 1. Ventas al contado realizadas hoy
SELECT '=== VENTAS AL CONTADO HOY ===' as seccion;
SELECT
    COUNT(*) as total_ventas_hoy,
    COALESCE(SUM(total), 0) as monto_total_ventas_hoy,
    MIN(created_at) as primera_venta_hoy,
    MAX(created_at) as ultima_venta_hoy
FROM ventas_contado
WHERE DATE(created_at) = CURRENT_DATE;

-- Detalles de ventas al contado de hoy
SELECT
    id,
    folio_venta,
    customer_name as cliente,
    total,
    created_at,
    vendedor_id
FROM ventas_contado
WHERE DATE(created_at) = CURRENT_DATE
ORDER BY created_at DESC;

-- 2. Apartados realizados hoy
SELECT '=== APARTADOS HOY ===' as seccion;
SELECT
    COUNT(*) as total_apartados_hoy,
    COALESCE(SUM(total), 0) as monto_total_apartados_hoy,
    COUNT(CASE WHEN credit_status = 'pendiente' THEN 1 END) as apartados_pendientes,
    COUNT(CASE WHEN credit_status = 'pagado' THEN 1 END) as apartados_pagados
FROM apartados
WHERE DATE(created_at) = CURRENT_DATE;

-- Detalles de apartados de hoy
SELECT
    id,
    folio_apartado,
    customer_name as cliente,
    total,
    amount_paid as pagado,
    credit_status as estado,
    created_at
FROM apartados
WHERE DATE(created_at) = CURRENT_DATE
ORDER BY created_at DESC;

-- 3. Pedidos realizados hoy
SELECT '=== PEDIDOS HOY ===' as seccion;
SELECT
    COUNT(*) as total_pedidos_hoy,
    COALESCE(SUM(total), 0) as monto_total_pedidos_hoy,
    COUNT(CASE WHEN estado = 'pendiente' THEN 1 END) as pedidos_pendientes,
    COUNT(CASE WHEN estado = 'confirmado' THEN 1 END) as pedidos_confirmados
FROM pedidos
WHERE DATE(created_at) = CURRENT_DATE;

-- Detalles de pedidos de hoy
SELECT
    id,
    folio_pedido,
    cliente_nombre as cliente,
    total,
    anticipo_pagado,
    saldo_pendiente,
    estado,
    tipo_pedido,
    created_at
FROM pedidos
WHERE DATE(created_at) = CURRENT_DATE
ORDER BY created_at DESC;

-- 4. Pagos realizados hoy
SELECT '=== PAGOS REALIZADOS HOY ===' as seccion;
SELECT 'Pagos generales' as tipo, COUNT(*) as cantidad, COALESCE(SUM(amount), 0) as total
FROM payments
WHERE DATE(created_at) = CURRENT_DATE
UNION ALL
SELECT 'Pagos de crédito', COUNT(*), COALESCE(SUM(amount), 0)
FROM credit_payments
WHERE DATE(created_at) = CURRENT_DATE
UNION ALL
SELECT 'Pagos de pedidos', COUNT(*), COALESCE(SUM(monto), 0)
FROM pagos_pedido
WHERE DATE(created_at) = CURRENT_DATE;

-- 5. Clientes registrados hoy
SELECT '=== CLIENTES REGISTRADOS HOY ===' as seccion;
SELECT
    COUNT(*) as total_clientes_hoy
FROM customers
WHERE DATE(created_at) = CURRENT_DATE;

-- Detalles de clientes registrados hoy
SELECT
    id,
    name as nombre,
    phone as telefono,
    created_at
FROM customers
WHERE DATE(created_at) = CURRENT_DATE
ORDER BY created_at DESC;

-- 6. Resumen general del día
SELECT '=== RESUMEN GENERAL DEL DÍA ===' as seccion;
SELECT
    'Ventas al contado' as tipo,
    COUNT(*) as cantidad,
    COALESCE(SUM(total), 0) as monto_total
FROM ventas_contado
WHERE DATE(created_at) = CURRENT_DATE
UNION ALL
SELECT
    'Apartados',
    COUNT(*),
    COALESCE(SUM(total), 0)
FROM apartados
WHERE DATE(created_at) = CURRENT_DATE
UNION ALL
SELECT
    'Pedidos',
    COUNT(*),
    COALESCE(SUM(total), 0)
FROM pedidos
WHERE DATE(created_at) = CURRENT_DATE
UNION ALL
SELECT
    'Clientes nuevos',
    COUNT(*),
    0
FROM customers
WHERE DATE(created_at) = CURRENT_DATE;
