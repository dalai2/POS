-- Simple fix for anticipo tickets in GestionPedidos
-- Execute this in pgAdmin on production database

-- For pedidos #7 and #10 (contado), create 'payment' kind tickets
-- Copying HTML from existing 'pedido-payment-*' tickets

-- Fix for pedido #7
INSERT INTO tickets (tenant_id, pedido_id, kind, html, created_at)
SELECT
  (SELECT tenant_id FROM pedidos WHERE id = 7 LIMIT 1) as tenant_id,
  7 as pedido_id,
  'payment' as kind,
  t.html,
  t.created_at
FROM tickets t
WHERE t.pedido_id = 7
  AND t.kind = 'pedido-payment-14'  -- The payment ID we saw in the diagnostic
  AND NOT EXISTS (SELECT 1 FROM tickets WHERE pedido_id = 7 AND kind = 'payment');

-- Fix for pedido #10
INSERT INTO tickets (tenant_id, pedido_id, kind, html, created_at)
SELECT
  (SELECT tenant_id FROM pedidos WHERE id = 10 LIMIT 1) as tenant_id,
  10 as pedido_id,
  'payment' as kind,
  t.html,
  t.created_at
FROM tickets t
WHERE t.pedido_id = 10
  AND t.kind = 'pedido-payment-17'  -- The payment ID we saw in the diagnostic
  AND NOT EXISTS (SELECT 1 FROM tickets WHERE pedido_id = 10 AND kind = 'payment');

-- Verify the fix
SELECT 'Tickets after fix:' as status;
SELECT id, pedido_id, kind, created_at
FROM tickets
WHERE pedido_id IN (7, 10)
ORDER BY pedido_id, kind;
