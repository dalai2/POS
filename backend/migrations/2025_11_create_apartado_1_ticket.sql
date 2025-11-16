-- Create initial ticket for apartado #1
-- This ticket should be the anticipo inicial (payment #2)

BEGIN;

-- Get apartado #1 data
SELECT 'Apartado #1 data:' as section;
SELECT a.id, a.customer_name, a.total, a.amount_paid, a.folio_apartado, a.created_at
FROM apartados a WHERE a.id = 1;

-- Get items for apartado #1
SELECT 'Items apartado #1:' as section;
SELECT id, apartado_id, quantity, amount, customer_name FROM items_apartado WHERE apartado_id = 1;

-- Get initial payment (payment #2)
SELECT 'Payment #2:' as section;
SELECT id, apartado_id, amount, payment_method, created_at FROM credit_payments WHERE id = 2;

-- Insert the initial ticket for apartado #1 with kind='payment'
-- This is the anticipo inicial ticket
INSERT INTO tickets (tenant_id, sale_id, pedido_id, kind, html, created_at)
SELECT
  a.tenant_id,
  NULL as sale_id,
  NULL as pedido_id,
  'payment' as kind,
  '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ticket Apartado 1</title></head><body><p>Ticket inicial para apartado #1 - Anticipo: $500.00</p></body></html>' as html,
  NOW() as created_at
FROM apartados a
WHERE a.id = 1
  AND NOT EXISTS (SELECT 1 FROM tickets WHERE kind = 'payment' AND created_at > NOW() - INTERVAL '1 minute');

SELECT 'Ticket created for apartado #1' as result;

-- Verify
SELECT 'Verify - All tickets:' as section;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at FROM tickets ORDER BY id DESC LIMIT 5;

COMMIT;

