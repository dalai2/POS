-- ============================================================================
-- DIAGNÓSTICO: Investigar problema de tickets incorrectos en apartados
-- ============================================================================
-- Este script ayuda a diagnosticar por qué se muestran tickets incorrectos
-- en la gestión de apartados (ventas a crédito)
-- ============================================================================

-- 1. Ver todas las ventas a crédito con sus tickets
SELECT 
    s.id as sale_id,
    s.folio_apartado,
    s.customer_name,
    s.total,
    s.amount_paid,
    (s.total - COALESCE(s.amount_paid, 0)) as balance,
    s.credit_status,
    s.tipo_venta,
    COUNT(DISTINCT t.id) as num_tickets,
    STRING_AGG(DISTINCT t.kind, ', ') as ticket_kinds
FROM sales s
LEFT JOIN tickets t ON t.sale_id = s.id
WHERE s.tipo_venta = 'credito'
GROUP BY s.id, s.folio_apartado, s.customer_name, s.total, s.amount_paid, s.credit_status, s.tipo_venta
ORDER BY s.id DESC
LIMIT 20;

-- 2. Ver tickets que podrían estar mal vinculados (sale_id no existe)
SELECT 
    t.id as ticket_id,
    t.sale_id,
    t.kind,
    t.created_at,
    s.id as actual_sale_id,
    s.tipo_venta
FROM tickets t
LEFT JOIN sales s ON t.sale_id = s.id
WHERE t.sale_id IS NOT NULL
  AND s.id IS NULL
ORDER BY t.id DESC
LIMIT 20;

-- 3. Ver si hay colisiones de IDs entre sales y pedidos
SELECT 
    'Collision' as type,
    s.id,
    s.tipo_venta,
    s.total as sale_total,
    p.tipo_pedido,
    p.total as pedido_total
FROM sales s
INNER JOIN pedidos p ON s.id = p.id
ORDER BY s.id DESC
LIMIT 20;

-- 4. Ver el apartado #10 específicamente si existe
SELECT 
    s.id,
    s.folio_apartado,
    s.customer_name,
    s.total,
    s.tipo_venta,
    s.created_at
FROM sales s
WHERE s.id = 10
  AND s.tipo_venta = 'credito';

-- 5. Ver tickets asociados al apartado #10
SELECT 
    t.id as ticket_id,
    t.kind,
    t.created_at,
    LENGTH(t.html) as html_size
FROM tickets t
WHERE t.sale_id = 10
ORDER BY t.created_at;

-- 6. Ver si hay un pedido con ID 10 que podría estar causando conflicto
SELECT 
    p.id,
    p.tipo_pedido,
    p.total,
    p.cliente_nombre,
    p.created_at
FROM pedidos p
WHERE p.id = 10;

-- 7. Verificar la secuencia de sales
SELECT 
    'Sales sequence info' as info,
    last_value as current_sequence_value,
    is_called
FROM sales_id_seq;

-- 8. Ver el rango de IDs de sales y pedidos
SELECT 
    'Sales' as table_name,
    MIN(id) as min_id,
    MAX(id) as max_id,
    COUNT(*) as total_records
FROM sales
UNION ALL
SELECT 
    'Pedidos' as table_name,
    MIN(id) as min_id,
    MAX(id) as max_id,
    COUNT(*) as total_records
FROM pedidos;

