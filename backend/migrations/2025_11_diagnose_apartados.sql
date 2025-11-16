-- Check if there's a separate apartados table
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE '%apartado%';

-- Check sales with tipo_venta = 'credito'
SELECT '=== SALES CON TIPO_VENTA = CREDITO ===' as section;
SELECT id, customer_name, total, amount_paid, folio_apartado, tipo_venta, credit_status, created_at 
FROM sales WHERE tipo_venta = 'credito' ORDER BY id;

-- Check all credit_payments
SELECT '=== TODOS LOS CREDIT PAYMENTS ===' as section;
SELECT id, sale_id, apartado_id, amount, payment_method, created_at 
FROM credit_payments ORDER BY id;

-- Check relationship between credit_payments and sales
SELECT '=== CREDIT PAYMENTS vs SALES ===' as section;
SELECT cp.id, cp.sale_id, cp.apartado_id, cp.amount, 
       s.id as sales_id, s.customer_name, s.folio_apartado
FROM credit_payments cp
LEFT JOIN sales s ON (cp.sale_id = s.id OR cp.apartado_id = s.id)
ORDER BY cp.id;

-- Check which sales have credit_payments
SELECT '=== SALES CON PAYMENTS ===' as section;
SELECT s.id, s.customer_name, s.total, s.amount_paid,
       COUNT(DISTINCT cp.id) as payment_count,
       GROUP_CONCAT(DISTINCT cp.id::text, ',') as payment_ids
FROM sales s
LEFT JOIN credit_payments cp ON (s.id = cp.sale_id OR s.id = cp.apartado_id)
WHERE s.tipo_venta = 'credito'
GROUP BY s.id, s.customer_name, s.total, s.amount_paid
ORDER BY s.id;

-- Check ticket #1 in detail
SELECT '=== TICKET #1 DETAIL ===' as section;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, SUBSTRING(html, 1, 300) as preview
FROM tickets WHERE id = 1;

-- Check ticket #39 (payment-2 para apartado #1)
SELECT '=== TICKET #39 (payment-2) ===' as section;
SELECT t.id, t.sale_id, t.pedido_id, t.kind, 
       cp.id as cp_id, cp.apartado_id, cp.sale_id as cp_sale_id,
       SUBSTRING(t.html, 1, 300) as preview
FROM tickets t
LEFT JOIN credit_payments cp ON (cp.id = 2)
WHERE t.id = 39;

-- Check all payment-X tickets and their credit_payments
SELECT '=== PAYMENT-X TICKETS ===' as section;
SELECT t.id, t.kind, 
       CAST(SUBSTRING(t.kind FROM 9) AS INTEGER) as extracted_payment_id,
       cp.id, cp.apartado_id, cp.sale_id, cp.amount
FROM tickets t
LEFT JOIN credit_payments cp ON (cp.id = CAST(SUBSTRING(t.kind FROM 9) AS INTEGER))
WHERE t.kind LIKE 'payment-%'
ORDER BY t.id;

-- Check sale_items for apartado #2 to find product_snapshot issue
SELECT '=== SALE_ITEMS APARTADO #2 ===' as section;
SELECT id, sale_id, product_id, name, codigo, quantity, 
       CASE WHEN product_snapshot IS NULL THEN 'NULL' ELSE 'HAS DATA' END as snapshot_status
FROM sale_items WHERE sale_id = 2;

-- Check if ticket #62 (payment-5 for apartado #2) has the product description issue
SELECT '=== TICKET #62 (payment-5) HTML ===' as section;
SELECT id, kind, LENGTH(html) as html_len, SUBSTRING(html, 1, 1000) as preview
FROM tickets WHERE id = 62;

