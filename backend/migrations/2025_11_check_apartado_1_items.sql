-- Check apartado #1 items and product snapshots

SELECT '=== APARTADO #1 ITEMS ===' as section;
SELECT id, apartado_id, product_id, quantity, amount, customer_name, product_snapshot 
FROM items_apartado WHERE apartado_id = 1;

SELECT '=== PRODUCTS TABLE ===' as section;
SELECT id, name, modelo, codigo 
FROM products LIMIT 10;

SELECT '=== SALE_ITEMS (for reference) ===' as section;
SELECT id, sale_id, product_id, name, codigo, quantity, product_snapshot 
FROM sale_items WHERE sale_id IN (1, 2) LIMIT 10;

