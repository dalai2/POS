-- Migration: Move pedido tickets from sale_id to pedido_id
-- This fixes tickets that were incorrectly stored with sale_id when they should use pedido_id

-- Update tickets where:
-- 1. The kind suggests it's a pedido ticket (starts with 'pedido' or is 'payment')
-- 2. The sale_id matches a pedido.id
-- 3. Either there's no sale with that id, or the sale has a different tipo_venta

-- First, identify pedido tickets by kind pattern
UPDATE tickets t
SET 
    pedido_id = t.sale_id,
    sale_id = NULL
WHERE 
    t.pedido_id IS NULL
    AND t.sale_id IS NOT NULL
    AND (
        t.kind LIKE 'pedido%'
        OR (
            t.kind IN ('payment', 'sale')
            AND EXISTS (
                SELECT 1 FROM pedidos p 
                WHERE p.id = t.sale_id 
                AND p.tipo_pedido = 'contado'
            )
            AND NOT EXISTS (
                SELECT 1 FROM sales s
                WHERE s.id = t.sale_id
                AND s.tipo_venta = 'contado'
            )
        )
    );

-- Report on the migration
SELECT 
    COUNT(*) as tickets_migrated,
    STRING_AGG(DISTINCT kind, ', ') as ticket_kinds
FROM tickets 
WHERE pedido_id IS NOT NULL;

