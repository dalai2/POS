-- DIAGNOSTICS - Read Only
-- Execute each section separately to see results

SELECT '=== PROBLEMA 1: Apartado #2 ===' as section;

SELECT id, customer_name, total, amount_paid, tipo_venta, credit_status, created_at 
FROM sales WHERE id = 2;

SELECT id, sale_id, name, codigo, quantity, product_snapshot 
FROM sale_items WHERE sale_id = 2;

SELECT id, apartado_id, amount, payment_method, created_at 
FROM credit_payments WHERE apartado_id = 2 ORDER BY created_at;

SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at 
FROM tickets WHERE sale_id = 2 ORDER BY created_at;

SELECT '=== PROBLEMA 2: Ticket #1 ===' as section;

SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len FROM tickets WHERE id = 1;

SELECT id, customer_name, total, tipo_venta FROM sales 
WHERE id = (SELECT sale_id FROM tickets WHERE id = 1 LIMIT 1);

SELECT id, cliente_nombre, total, tipo_pedido FROM pedidos 
WHERE id = (SELECT pedido_id FROM tickets WHERE id = 1 LIMIT 1);

SELECT '=== PROBLEMA 3: Apartado #1 ===' as section;

SELECT id, customer_name, total, amount_paid, tipo_venta FROM sales WHERE id = 1;

SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len FROM tickets 
WHERE sale_id = 1 OR pedido_id = 1 ORDER BY created_at;

SELECT id, kind FROM tickets WHERE kind LIKE 'payment-%' LIMIT 10;

SELECT '=== PROBLEMA 4: Apartado #2 - Tickets ===' as section;

SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len FROM tickets 
WHERE sale_id = 2 ORDER BY created_at;

SELECT '=== PROBLEMA 5: Venta #8 - Fecha ===' as section;

SELECT id, customer_name, total, created_at, 
       CAST(created_at AS DATE) as date_utc,
       created_at AT TIME ZONE 'America/Mexico_City' as created_at_mx
FROM sales WHERE id = 8;

SELECT current_setting('timezone') as db_timezone;

SELECT '=== RESUMEN: Todos los Tickets ===' as section;

SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at 
FROM tickets ORDER BY id;

SELECT '=== RESUMEN: Apartados (Sales Credito) ===' as section;

SELECT s.id, s.customer_name, s.total, s.amount_paid, 
       COUNT(DISTINCT si.id) as items,
       COUNT(DISTINCT cp.id) as payments,
       COUNT(DISTINCT t.id) as tickets
FROM sales s
LEFT JOIN sale_items si ON s.id = si.sale_id
LEFT JOIN credit_payments cp ON s.id = cp.apartado_id
LEFT JOIN tickets t ON s.id = t.sale_id
WHERE s.tipo_venta = 'credito'
GROUP BY s.id, s.customer_name, s.total, s.amount_paid
ORDER BY s.id;

SELECT '=== RESUMEN: Pedidos ===' as section;

SELECT p.id, p.cliente_nombre, p.total, p.anticipo_pagado, p.tipo_pedido,
       COUNT(DISTINCT pp.id) as pagos,
       COUNT(DISTINCT t.id) as tickets
FROM pedidos p
LEFT JOIN pagos_pedido pp ON p.id = pp.pedido_id
LEFT JOIN tickets t ON p.id = t.pedido_id
GROUP BY p.id, p.cliente_nombre, p.total, p.anticipo_pagado, p.tipo_pedido
ORDER BY p.id;
