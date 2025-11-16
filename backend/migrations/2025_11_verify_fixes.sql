-- Verify all fixes were applied

SELECT '=== VERIFICACION FIX 2: product_snapshot actualizado ===' as section;
SELECT id, sale_id, product_id, name, codigo, 
       CASE WHEN product_snapshot IS NULL THEN 'NULL' ELSE 'HAS DATA' END as snapshot_status
FROM sale_items WHERE sale_id = 2;

SELECT '=== TICKETS APARTADO #2 ===' as section;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at
FROM tickets WHERE sale_id = 2 ORDER BY created_at;

SELECT '=== APARTADOS SUMMARY ===' as section;
SELECT a.id, a.customer_name, a.total, a.amount_paid,
       COUNT(DISTINCT ia.id) as items,
       COUNT(DISTINCT ap.id) as payments
FROM apartados a
LEFT JOIN items_apartado ia ON a.id = ia.apartado_id
LEFT JOIN credit_payments ap ON a.id = ap.apartado_id
GROUP BY a.id, a.customer_name, a.total, a.amount_paid
ORDER BY a.id;

SELECT '=== TICKET #39 DETAIL ===' as section;
SELECT id, sale_id, pedido_id, kind, SUBSTRING(html, 1, 500) as html_preview
FROM tickets WHERE id = 39;

SELECT '=== TICKET #62 DETAIL ===' as section;
SELECT id, sale_id, pedido_id, kind, SUBSTRING(html, 1, 500) as html_preview
FROM tickets WHERE id = 62;

SELECT '=== PEDIDOS CONTADO ===' as section;
SELECT p.id, p.cliente_nombre, p.total, p.anticipo_pagado, p.tipo_pedido,
       COUNT(DISTINCT t.id) as tickets
FROM pedidos p
LEFT JOIN tickets t ON p.id = t.pedido_id
WHERE p.tipo_pedido = 'contado'
GROUP BY p.id, p.cliente_nombre, p.total, p.anticipo_pagado, p.tipo_pedido
ORDER BY p.id;

