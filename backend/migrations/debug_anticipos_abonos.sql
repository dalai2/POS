-- Script de depuración para verificar anticipos y abonos
-- Reemplaza las fechas con el periodo que estás consultando

-- 1. Apartados creados en el periodo con sus pagos iniciales (anticipos)
SELECT 'APARTADOS Y SUS ANTICIPOS INICIALES (Payment)' as info;
SELECT 
    s.id as sale_id,
    s.created_at as apartado_created_at,
    s.tipo_venta,
    s.total,
    s.amount_paid,
    s.credit_status,
    p.id as payment_id,
    p.method,
    p.amount,
    s.created_at::date as fecha_apartado
FROM sales s
LEFT JOIN payments p ON p.sale_id = s.id
WHERE s.tenant_id = 1  -- Cambia según tu tenant
  AND s.tipo_venta = 'credito'
  AND s.created_at >= '2025-11-15 00:00:00-06:00'  -- Fecha inicio: 15 nov 2025
  AND s.created_at <= '2025-11-15 23:59:59-06:00'  -- Fecha fin: 15 nov 2025
ORDER BY s.created_at DESC;

-- 2. Abonos a apartados (CreditPayment) creados en el periodo
SELECT 'ABONOS A APARTADOS (CreditPayment)' as info;
SELECT 
    cp.id as credit_payment_id,
    cp.sale_id,
    cp.amount,
    cp.payment_method,
    cp.created_at,
    cp.created_at::date as fecha_abono,
    s.created_at as apartado_created_at,
    s.credit_status
FROM credit_payments cp
JOIN sales s ON s.id = cp.sale_id
WHERE cp.tenant_id = 1  -- Cambia según tu tenant
  AND s.tipo_venta = 'credito'
  AND cp.created_at >= '2025-11-14 00:00:00-06:00'  -- Cambia por tu fecha inicio
  AND cp.created_at <= '2025-11-14 23:59:59-06:00'  -- Cambia por tu fecha fin
ORDER BY cp.created_at DESC;

-- 3. Pedidos apartados y sus anticipos (PagoPedido tipo 'anticipo') creados en el periodo
SELECT 'PEDIDOS APARTADOS Y SUS ANTICIPOS (PagoPedido)' as info;
SELECT 
    pe.id as pedido_id,
    pe.created_at as pedido_created_at,
    pe.tipo_pedido,
    pe.estado,
    pe.total,
    pe.anticipo_pagado,
    pe.saldo_pendiente,
    pp.id as pago_id,
    pp.tipo_pago,
    pp.monto,
    pp.metodo_pago,
    pp.created_at as pago_created_at,
    pp.created_at::date as fecha_anticipo
FROM pedidos pe
LEFT JOIN pagos_pedido pp ON pp.pedido_id = pe.id AND pp.tipo_pago = 'anticipo'
WHERE pe.tenant_id = 1  -- Cambia según tu tenant
  AND pe.tipo_pedido = 'apartado'
  AND pp.created_at >= '2025-11-14 00:00:00-06:00'  -- Cambia por tu fecha inicio
  AND pp.created_at <= '2025-11-14 23:59:59-06:00'  -- Cambia por tu fecha fin
ORDER BY pp.created_at DESC;

-- 4. Abonos a pedidos apartados (PagoPedido tipo 'saldo') creados en el periodo
SELECT 'ABONOS A PEDIDOS APARTADOS (PagoPedido tipo saldo)' as info;
SELECT 
    pp.id as pago_id,
    pp.pedido_id,
    pp.tipo_pago,
    pp.monto,
    pp.metodo_pago,
    pp.created_at,
    pp.created_at::date as fecha_abono,
    pe.created_at as pedido_created_at,
    pe.estado,
    pe.tipo_pedido
FROM pagos_pedido pp
JOIN pedidos pe ON pe.id = pp.pedido_id
WHERE pe.tenant_id = 1  -- Cambia según tu tenant
  AND pe.tipo_pedido = 'apartado'
  AND pp.tipo_pago = 'saldo'
  AND pp.created_at >= '2025-11-14 00:00:00-06:00'  -- Cambia por tu fecha inicio
  AND pp.created_at <= '2025-11-14 23:59:59-06:00'  -- Cambia por tu fecha fin
ORDER BY pp.created_at DESC;

-- 5. Resumen de totales
SELECT 'RESUMEN DE TOTALES' as info;
SELECT 
    (SELECT COALESCE(SUM(p.amount), 0) FROM payments p
     JOIN sales s ON s.id = p.sale_id
     WHERE s.tenant_id = 1 AND s.tipo_venta = 'credito'
     AND s.created_at >= '2025-11-14 00:00:00-06:00'
     AND s.created_at <= '2025-11-14 23:59:59-06:00') as anticipos_apartados_total,
    
    (SELECT COUNT(*) FROM payments p
     JOIN sales s ON s.id = p.sale_id
     WHERE s.tenant_id = 1 AND s.tipo_venta = 'credito'
     AND s.created_at >= '2025-11-14 00:00:00-06:00'
     AND s.created_at <= '2025-11-14 23:59:59-06:00') as anticipos_apartados_count,
    
    (SELECT COALESCE(SUM(pp.monto), 0) FROM pagos_pedido pp
     JOIN pedidos pe ON pe.id = pp.pedido_id
     WHERE pe.tenant_id = 1 AND pe.tipo_pedido = 'apartado'
     AND pp.tipo_pago = 'anticipo'
     AND pp.created_at >= '2025-11-14 00:00:00-06:00'
     AND pp.created_at <= '2025-11-14 23:59:59-06:00') as anticipos_pedidos_total,
    
    (SELECT COUNT(*) FROM pagos_pedido pp
     JOIN pedidos pe ON pe.id = pp.pedido_id
     WHERE pe.tenant_id = 1 AND pe.tipo_pedido = 'apartado'
     AND pp.tipo_pago = 'anticipo'
     AND pp.created_at >= '2025-11-14 00:00:00-06:00'
     AND pp.created_at <= '2025-11-14 23:59:59-06:00') as anticipos_pedidos_count,
    
    (SELECT COALESCE(SUM(cp.amount), 0) FROM credit_payments cp
     JOIN sales s ON s.id = cp.sale_id
     WHERE cp.tenant_id = 1 AND s.tipo_venta = 'credito'
     AND cp.created_at >= '2025-11-14 00:00:00-06:00'
     AND cp.created_at <= '2025-11-14 23:59:59-06:00') as abonos_apartados_total,
    
    (SELECT COUNT(*) FROM credit_payments cp
     JOIN sales s ON s.id = cp.sale_id
     WHERE cp.tenant_id = 1 AND s.tipo_venta = 'credito'
     AND cp.created_at >= '2025-11-14 00:00:00-06:00'
     AND cp.created_at <= '2025-11-14 23:59:59-06:00') as abonos_apartados_count,
    
    (SELECT COALESCE(SUM(pp.monto), 0) FROM pagos_pedido pp
     JOIN pedidos pe ON pe.id = pp.pedido_id
     WHERE pe.tenant_id = 1 AND pe.tipo_pedido = 'apartado'
     AND pp.tipo_pago = 'saldo'
     AND pp.created_at >= '2025-11-14 00:00:00-06:00'
     AND pp.created_at <= '2025-11-14 23:59:59-06:00') as abonos_pedidos_total,
    
    (SELECT COUNT(*) FROM pagos_pedido pp
     JOIN pedidos pe ON pe.id = pp.pedido_id
     WHERE pe.tenant_id = 1 AND pe.tipo_pedido = 'apartado'
     AND pp.tipo_pago = 'saldo'
     AND pp.created_at >= '2025-11-14 00:00:00-06:00'
     AND pp.created_at <= '2025-11-14 23:59:59-06:00') as abonos_pedidos_count;

