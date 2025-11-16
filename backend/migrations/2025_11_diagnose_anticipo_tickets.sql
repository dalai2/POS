-- Diagnostic script to check anticipo (initial payment) tickets in GestionPedidos
-- For pedidos #10 and #7 that show "Regenerar" button
-- Compatible with pgAdmin (PostgreSQL syntax)

SELECT '=== ANTICIPO TICKETS DIAGNOSIS ===' as title;

-- ============================================================================
-- SECTION 1: Check Pedidos #10 and #7
-- ============================================================================

SELECT 'SECTION 1: Pedidos Details (#7 and #10)' as section;

  SELECT
    id,
    user_id,
    cliente_nombre,
    cantidad,
    precio_unitario,
    total,
    anticipo_pagado,
    saldo_pendiente,
    estado,
    tipo_pedido,
    created_at
  FROM pedidos
  WHERE id IN (7, 10)
  ORDER BY id;

-- ============================================================================
-- SECTION 2: Check Payments for these Pedidos
-- ============================================================================

SELECT 'SECTION 2: Payments linked to Pedidos #7 and #10' as section;

SELECT
  p.id as payment_id,
  p.pedido_id,
  p.monto as amount,
  p.metodo_pago as method,
  p.tipo_pago as payment_type,
  p.created_at
FROM pagos_pedido p
WHERE p.pedido_id IN (7, 10)
ORDER BY p.pedido_id, p.created_at;

-- ============================================================================
-- SECTION 3: Check Tickets linked to these Pedidos
-- ============================================================================

SELECT 'SECTION 3: Tickets for Pedidos #7 and #10' as section;

SELECT 
  t.id as ticket_id,
  t.pedido_id,
  t.kind,
  t.sale_id,
  t.created_at,
  LENGTH(t.html) as html_length,
  CASE 
    WHEN t.html LIKE '%ANTICIPO%' THEN 'Contains ANTICIPO'
    WHEN t.html LIKE '%PAGO%' THEN 'Contains PAGO'
    WHEN t.html LIKE '%FOLIO%' THEN 'Contains FOLIO'
    ELSE 'Other content'
  END as html_type
FROM tickets t
WHERE t.pedido_id IN (7, 10)
ORDER BY t.pedido_id, t.created_at;

-- ============================================================================
-- SECTION 4: Check for orphaned tickets (kind but no pedido_id match)
-- ============================================================================

SELECT 'SECTION 4: Payment Tickets vs Actual Payments' as section;

SELECT
  t.id as ticket_id,
  t.pedido_id,
  t.kind,
  CASE
    WHEN t.kind LIKE 'payment-%' THEN CAST(SUBSTRING(t.kind FROM 9) AS INTEGER)
    ELSE NULL
  END as payment_id_from_kind,
  EXISTS (
    SELECT 1 FROM pagos_pedido pp
    WHERE pp.id = CASE WHEN t.kind LIKE 'payment-%' THEN CAST(SUBSTRING(t.kind FROM 9) AS INTEGER) ELSE NULL END
  ) as payment_exists
FROM tickets t
WHERE t.pedido_id IN (7, 10)
ORDER BY t.pedido_id, t.id;

-- ============================================================================
-- SECTION 5: Full Ticket Content Preview (first 500 chars)
-- ============================================================================

SELECT 'SECTION 5: Ticket HTML Preview (first 500 chars)' as section;

SELECT 
  t.id as ticket_id,
  t.pedido_id,
  t.kind,
  SUBSTRING(t.html, 1, 500) as html_preview
FROM tickets t
WHERE t.pedido_id IN (7, 10)
ORDER BY t.pedido_id, t.created_at;

-- ============================================================================
-- SECTION 6: Check if payments exist but no tickets
-- ============================================================================

SELECT 'SECTION 6: Payments WITHOUT tickets' as section;

SELECT 
  p.id as payment_id,
  p.pedido_id,
  p.monto,
  p.created_at,
  'NO TICKET FOUND' as status
FROM pagos_pedido p
WHERE p.pedido_id IN (7, 10)
  AND NOT EXISTS (
    SELECT 1 FROM tickets t 
    WHERE (t.pedido_id = p.pedido_id OR t.kind = 'payment-' || p.id)
  )
ORDER BY p.pedido_id;

-- ============================================================================
-- SECTION 7: Summary for Frontend Debug
-- ============================================================================

SELECT 'SECTION 7: Summary - What Frontend Expects' as section;

SELECT
  p.id as pedido_id,
  p.cliente_nombre,
  COUNT(DISTINCT pp_payments.id) as expected_payments,
  COUNT(DISTINCT t.id) as actual_tickets,
  STRING_AGG(DISTINCT 'pedido-payment-' || pp_payments.id, ', ') as expected_ticket_kinds
FROM pedidos p
LEFT JOIN pagos_pedido pp_payments ON p.id = pp_payments.pedido_id
LEFT JOIN tickets t ON (t.pedido_id = p.id OR t.kind LIKE 'pedido-payment-%')
WHERE p.id IN (7, 10)
GROUP BY p.id, p.cliente_nombre
ORDER BY p.id;


