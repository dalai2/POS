-- Migration: Add pedido_id column to tickets table
-- This allows tickets to be linked to both sales and pedidos separately

-- Add the pedido_id column
ALTER TABLE tickets
ADD COLUMN pedido_id INTEGER;

-- Add foreign key constraint
ALTER TABLE tickets
ADD CONSTRAINT tickets_pedido_id_fkey 
FOREIGN KEY (pedido_id) REFERENCES pedidos(id);

-- Add index for performance
CREATE INDEX IF NOT EXISTS ix_tickets_pedido_id ON tickets(pedido_id);

-- Update unique constraint to handle both sale_id and pedido_id
-- Drop the old constraint first
ALTER TABLE tickets DROP CONSTRAINT IF EXISTS uq_ticket_tenant_sale_kind;

-- Add new constraint that works with either sale_id or pedido_id
-- Note: We can't have a simple unique constraint because we need to handle NULL values
-- Instead, we'll create a partial unique index
CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_tenant_sale_kind 
ON tickets(tenant_id, sale_id, kind) 
WHERE sale_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_tenant_pedido_kind 
ON tickets(tenant_id, pedido_id, kind) 
WHERE pedido_id IS NOT NULL;

