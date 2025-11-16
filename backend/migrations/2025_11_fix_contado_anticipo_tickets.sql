-- Fix for anticipo tickets in GestionPedidos (pedidos de contado)
-- Problem: Tickets #7 and #10 show "Regenerar" but button doesn't work
-- Root cause: Tickets have kind='pedido-payment-*' but contado pedidos expect kind='payment'
-- These are "contado" pedidos that should have a single payment ticket with kind='payment'
--
-- Diagnosis summary:
-- Pedido #7 (LUIS VENEGAS): tipo_pedido='contado', anticipo_pagado=7500, ticket#45 has kind='pedido-payment-14'
-- Pedido #10 (FATIMA VALDIVIA): tipo_pedido='contado', anticipo_pagado=6500, ticket#60 has kind='pedido-payment-17'
--
-- Solution: Convert these to kind='payment' so they match the frontend filter for contado pedidos

-- Step 1: Verify the before state
SELECT '=== BEFORE FIX: Tickets for pedidos #7 and #10 ===' as section;
SELECT id, pedido_id, kind, created_at 
FROM tickets 
WHERE pedido_id IN (7, 10) 
ORDER BY pedido_id, kind;

-- Step 2: Update tickets from kind='pedido-payment-*' to kind='payment' for contado pedidos
UPDATE tickets 
SET kind = 'payment'
WHERE pedido_id IN (
  SELECT id FROM pedidos WHERE id IN (7, 10) AND tipo_pedido = 'contado'
) 
AND kind LIKE 'pedido-payment-%';

-- Step 3: Verify the after state
SELECT '=== AFTER FIX: Tickets for pedidos #7 and #10 ===' as section;
SELECT id, pedido_id, kind, created_at 
FROM tickets 
WHERE pedido_id IN (7, 10) 
ORDER BY pedido_id, kind;

-- Step 4: Verify pedido details
SELECT '=== Pedido Details ===' as section;
SELECT id, cliente_nombre, tipo_pedido, estado, anticipo_pagado, saldo_pendiente 
FROM pedidos 
WHERE id IN (7, 10);

-- Step 5: Verify pagos linked to these pedidos
SELECT '=== Pagos Details ===' as section;
SELECT id, pedido_id, monto, metodo_pago, tipo_pago, created_at 
FROM pagos_pedido 
WHERE pedido_id IN (7, 10) 
ORDER BY pedido_id, id;

