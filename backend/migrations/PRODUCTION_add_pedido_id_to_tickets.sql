-- ============================================================================
-- MIGRATION FOR PRODUCTION: Add pedido_id to tickets table
-- ============================================================================
-- This migration adds support for linking tickets to pedidos separately from sales
-- Run this in your production database AFTER testing in development
--
-- IMPORTANT: 
-- 1. Backup your database before running this migration
-- 2. Test this migration in a staging environment first
-- 3. This migration is idempotent (safe to run multiple times)
--
-- What this does:
-- - Adds pedido_id column to tickets table
-- - Adds foreign key constraint to pedidos table
-- - Creates indexes for performance
-- - Updates unique constraints to handle both sale_id and pedido_id
-- - Migrates existing pedido tickets from sale_id to pedido_id
-- ============================================================================

-- Start transaction for safety
BEGIN;

-- Step 1: Add the pedido_id column
ALTER TABLE tickets
ADD COLUMN IF NOT EXISTS pedido_id INTEGER;

-- Step 2: Add foreign key constraint (only if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'tickets_pedido_id_fkey'
    ) THEN
        ALTER TABLE tickets
        ADD CONSTRAINT tickets_pedido_id_fkey 
        FOREIGN KEY (pedido_id) REFERENCES pedidos(id);
    END IF;
END $$;

-- Step 3: Add index for performance (only if not exists)
CREATE INDEX IF NOT EXISTS ix_tickets_pedido_id ON tickets(pedido_id);

-- Step 4: Update unique constraints
-- Drop the old constraint if it exists
ALTER TABLE tickets DROP CONSTRAINT IF EXISTS uq_ticket_tenant_sale_kind;

-- Create new partial unique indexes
CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_tenant_sale_kind 
ON tickets(tenant_id, sale_id, kind) 
WHERE sale_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_tenant_pedido_kind 
ON tickets(tenant_id, pedido_id, kind) 
WHERE pedido_id IS NOT NULL;

-- Step 5: Migrate existing pedido tickets from sale_id to pedido_id
-- This updates tickets where:
-- 1. The kind suggests it's a pedido ticket (starts with 'pedido' or is 'payment')
-- 2. The sale_id matches a pedido.id
-- 3. Either there's no sale with that id, or the sale has a different tipo_venta

UPDATE tickets t
SET 
    pedido_id = t.sale_id,
    sale_id = NULL
WHERE 
    t.pedido_id IS NULL
    AND t.sale_id IS NOT NULL
    AND (
        -- Tickets with 'pedido' prefix are definitely pedido tickets
        t.kind LIKE 'pedido%'
        OR (
            -- Tickets with 'payment' or 'sale' kind that belong to contado pedidos
            t.kind IN ('payment', 'sale')
            AND EXISTS (
                SELECT 1 FROM pedidos p 
                WHERE p.id = t.sale_id 
                AND p.tipo_pedido = 'contado'
            )
            AND NOT EXISTS (
                -- Make sure there's no actual sale with the same id
                SELECT 1 FROM sales s
                WHERE s.id = t.sale_id
                AND s.tipo_venta = 'contado'
            )
        )
    );

-- Step 6: Report on the migration
SELECT 
    COUNT(*) as tickets_migrated,
    STRING_AGG(DISTINCT kind, ', ') as ticket_kinds
FROM tickets 
WHERE pedido_id IS NOT NULL;

-- Verify the results
SELECT 
    'Verification Report' as step,
    COUNT(CASE WHEN pedido_id IS NOT NULL THEN 1 END) as tickets_with_pedido_id,
    COUNT(CASE WHEN sale_id IS NOT NULL THEN 1 END) as tickets_with_sale_id,
    COUNT(*) as total_tickets
FROM tickets;

-- If everything looks good, commit the transaction
COMMIT;

-- If you need to rollback, run: ROLLBACK;

