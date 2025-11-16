-- Delete payment-2 ticket for apartado #2 to regenerate it with correct amounts

BEGIN;

SELECT '=== BEFORE: Tickets with kind payment-2 ===' as section;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at 
FROM tickets WHERE kind = 'payment-2';

-- Delete payment-2 ticket
DELETE FROM tickets WHERE kind = 'payment-2';

SELECT '=== AFTER: Tickets deleted ===' as section;
SELECT COUNT(*) as remaining_payment_2_tickets FROM tickets WHERE kind = 'payment-2';

COMMIT;

