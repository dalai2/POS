-- Delete ticket for apartado #1 to regenerate it

BEGIN;

SELECT '=== BEFORE: Tickets for apartado #1 ===' as section;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at 
FROM tickets WHERE sale_id = 1 OR kind = 'payment-2';

-- Delete payment-2 ticket (first payment for apartado #1)
DELETE FROM tickets WHERE kind = 'payment-2';

SELECT '=== AFTER: Tickets for apartado #1 ===' as section;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at 
FROM tickets WHERE sale_id = 1;

COMMIT;

