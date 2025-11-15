-- Script para debuggear abonos en Resumen por Vendedores
-- Asegúrate de cambiar las fechas al periodo que estés consultando

-- Variables del periodo (ajusta según tu consulta)
-- Ejemplo: 2025-11-15 para el 15 de noviembre de 2025

-- 1. Ver apartados pendientes/vencidos con abonos en el periodo
SELECT 
    'Apartados con abonos en periodo' as info,
    s.id as sale_id,
    s.vendedor_id,
    u.email as vendedor_email,
    s.credit_status,
    s.created_at as apartado_created,
    cp.id as abono_id,
    cp.amount as abono_monto,
    cp.payment_method,
    cp.created_at as abono_created
FROM sales s
JOIN credit_payments cp ON s.id = cp.sale_id
LEFT JOIN users u ON s.vendedor_id = u.id
WHERE s.tenant_id = 1
  AND s.tipo_venta = 'credito'
  AND s.credit_status IN ('pendiente', 'vencido')
  AND cp.created_at >= '2025-11-15 00:00:00-06:00'
  AND cp.created_at <= '2025-11-15 23:59:59-06:00'
ORDER BY s.id, cp.created_at;

-- 2. Ver pedidos apartados pendientes con abonos en el periodo
SELECT 
    'Pedidos con abonos en periodo' as info,
    p.id as pedido_id,
    p.user_id,
    u.email as vendedor_email,
    p.estado,
    p.created_at as pedido_created,
    pp.id as abono_id,
    pp.monto as abono_monto,
    pp.metodo_pago,
    pp.tipo_pago,
    pp.created_at as abono_created
FROM pedidos p
JOIN pagos_pedido pp ON p.id = pp.pedido_id
LEFT JOIN users u ON p.user_id = u.id
WHERE p.tenant_id = 1
  AND p.tipo_pedido = 'apartado'
  AND p.estado NOT IN ('pagado', 'entregado', 'cancelado')
  AND pp.tipo_pago = 'saldo'
  AND pp.created_at >= '2025-11-15 00:00:00-06:00'
  AND pp.created_at <= '2025-11-15 23:59:59-06:00'
ORDER BY p.id, pp.created_at;

-- 3. Verificar si hay apartados/pedidos que sean el último abono liquidante
SELECT 
    'Apartados liquidados en periodo (último abono)' as info,
    s.id as sale_id,
    s.vendedor_id,
    u.email as vendedor_email,
    cp.id as ultimo_abono_id,
    cp.amount as ultimo_abono_monto,
    cp.created_at as ultimo_abono_created
FROM sales s
JOIN credit_payments cp ON s.id = cp.sale_id
LEFT JOIN users u ON s.vendedor_id = u.id
WHERE s.tenant_id = 1
  AND s.tipo_venta = 'credito'
  AND s.credit_status = 'pagado'
  AND cp.created_at = (
    SELECT MAX(created_at) 
    FROM credit_payments 
    WHERE sale_id = s.id
  )
  AND cp.created_at >= '2025-11-15 00:00:00-06:00'
  AND cp.created_at <= '2025-11-15 23:59:59-06:00'
ORDER BY s.id;

-- 4. Verificar apartados pendientes creados en el periodo
SELECT 
    'Apartados pendientes creados en periodo' as info,
    s.id as sale_id,
    s.vendedor_id,
    u.email as vendedor_email,
    s.created_at,
    COUNT(cp.id) as num_abonos
FROM sales s
LEFT JOIN credit_payments cp ON s.id = cp.sale_id
LEFT JOIN users u ON s.vendedor_id = u.id
WHERE s.tenant_id = 1
  AND s.tipo_venta = 'credito'
  AND s.credit_status IN ('pendiente', 'vencido')
  AND s.created_at >= '2025-11-15 00:00:00-06:00'
  AND s.created_at <= '2025-11-15 23:59:59-06:00'
GROUP BY s.id, s.vendedor_id, u.email, s.created_at
ORDER BY s.id;

-- 5. Verificar pedidos pendientes creados en el periodo
SELECT 
    'Pedidos pendientes creados en periodo' as info,
    p.id as pedido_id,
    p.user_id,
    u.email as vendedor_email,
    p.created_at,
    COUNT(CASE WHEN pp.tipo_pago = 'saldo' THEN 1 END) as num_abonos
FROM pedidos p
LEFT JOIN pagos_pedido pp ON p.id = pp.pedido_id
LEFT JOIN users u ON p.user_id = u.id
WHERE p.tenant_id = 1
  AND p.tipo_pedido = 'apartado'
  AND p.estado NOT IN ('pagado', 'entregado', 'cancelado')
  AND p.created_at >= '2025-11-15 00:00:00-06:00'
  AND p.created_at <= '2025-11-15 23:59:59-06:00'
GROUP BY p.id, p.user_id, u.email, p.created_at
ORDER BY p.id;

