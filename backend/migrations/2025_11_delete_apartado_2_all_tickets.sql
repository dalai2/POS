-- Delete ALL tickets for apartado #2 to regenerate them

BEGIN;

SELECT '=== BEFORE: All tickets for apartado #2 ===' as section;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at 
FROM tickets WHERE sale_id = 2;

-- Delete all tickets with sale_id = 2
DELETE FROM tickets WHERE sale_id = 2;

SELECT '=== ALSO delete payment-X tickets linked to apartado #2 ===' as section;
SELECT id, kind FROM tickets WHERE kind LIKE 'payment-%' AND id IN (62);

-- Delete payment-5 ticket (second payment for apartado #2)
DELETE FROM tickets WHERE id = 62 OR kind = 'payment-5';

SELECT '=== AFTER: Tickets for apartado #2 ===' as section;
SELECT COUNT(*) as remaining_tickets FROM tickets WHERE sale_id = 2 OR kind = 'payment-5';

COMMIT;

