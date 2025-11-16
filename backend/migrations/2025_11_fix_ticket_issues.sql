-- FIX SCRIPT FOR TICKET ISSUES
-- Safe updates with verification

BEGIN;

-- ========================================
-- FIX 1: Ticket #39 - HTML dice "Pedido 10" pero es del apartado #1
-- ========================================

SELECT 'FIX 1: Checking Ticket #39 before fix' as step;
SELECT id, sale_id, pedido_id, kind, SUBSTRING(html, 1, 200) as preview
FROM tickets WHERE id = 39;

-- This ticket is for apartado #1 payment #2, but HTML says "Pedido 10"
-- We need to verify the HTML content and potentially regenerate it
-- For now, just document what we found:
-- Ticket #39: kind='payment-2', sale_id=NULL, pedido_id=1
-- This is WRONG - it should be sale_id=1 (the sale from apartados table) or the HTML should reference the correct apartado

SELECT 'FIX 1: Ticket #39 is linked to pedido_id=1 but should link to apartado #1' as issue;

-- ========================================
-- FIX 2: Apartment #2 - product_snapshot NULL in sale_items
-- ========================================

SELECT 'FIX 2: Checking sale_items for apartado #2 before fix' as step;
SELECT id, sale_id, product_id, name, codigo, product_snapshot 
FROM sale_items WHERE sale_id = 2;

-- Update: we found that sale_items.id=2 has NULL product_snapshot
-- We need to populate it from the item data we have
-- Item 2 is: "MEDALLA-ESPIRITU SANTO-florentino-10K-1.2g" code "R613"

UPDATE sale_items 
SET product_snapshot = jsonb_build_object(
  'id', product_id,
  'nombre', name,
  'codigo', codigo,
  'description', 'MEDALLA-ESPIRITU SANTO-florentino-10K-1.2g'
)
WHERE sale_id = 2 AND product_snapshot IS NULL AND name LIKE '%MEDALLA%';

SELECT 'FIX 2: Updated sale_items for apartado #2' as step;
SELECT id, sale_id, product_id, name, codigo, product_snapshot 
FROM sale_items WHERE sale_id = 2;

-- ========================================
-- FIX 3: Verify tickets for apartado #2
-- ========================================

SELECT 'FIX 3: Tickets for apartado #2' as step;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len
FROM tickets WHERE sale_id = 2 ORDER BY created_at;

-- ========================================
-- FIX 4: Timezone issue - just document
-- ========================================

SELECT 'FIX 4: Database is in UTC - frontend must convert to America/Mexico_City' as issue;
SELECT current_setting('timezone') as db_timezone;

-- ========================================
-- Verification
-- ========================================

SELECT 'VERIFICATION: Apartados after fixes' as step;
SELECT a.id, a.customer_name, a.total, a.amount_paid,
       COUNT(DISTINCT ia.id) as items,
       COUNT(DISTINCT ap.id) as payments
FROM apartados a
LEFT JOIN items_apartado ia ON a.id = ia.apartado_id
LEFT JOIN credit_payments ap ON a.id = ap.apartado_id
GROUP BY a.id, a.customer_name, a.total, a.amount_paid
ORDER BY a.id;

SELECT 'VERIFICATION: Tickets summary' as step;
SELECT id, sale_id, pedido_id, kind, LENGTH(html) as html_len, created_at
FROM tickets ORDER BY id;

COMMIT;

