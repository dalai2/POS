-- Fix Ticket #39: Wrong pedido_id and HTML says "Pedido 10"
-- It should be payment-2 for apartado #1, not pedido_id=1

BEGIN;

SELECT 'BEFORE: Ticket #39 has wrong structure' as step;
SELECT id, sale_id, pedido_id, kind, SUBSTRING(html, 1, 100) as preview FROM tickets WHERE id = 39;

-- Option: Delete ticket #39 to force regeneration from frontend
-- When user clicks the abono button in apartado #1, the system will regenerate the correct ticket
DELETE FROM tickets WHERE id = 39;

SELECT 'AFTER: Ticket #39 deleted - will regenerate from frontend' as step;
SELECT COUNT(*) as tickets_remaining FROM tickets WHERE id = 39;

COMMIT;

