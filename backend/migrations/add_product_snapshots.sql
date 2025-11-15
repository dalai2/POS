-- ============================================
-- Migration: Add JSONB snapshots for productos
-- ============================================

BEGIN;

-- Add producto_snapshot column to pedido_items
ALTER TABLE pedido_items
ADD COLUMN IF NOT EXISTS producto_snapshot JSONB;

-- Add product_snapshot column to sale_items
ALTER TABLE sale_items
ADD COLUMN IF NOT EXISTS product_snapshot JSONB;

-- Optional GIN indexes for faster JSONB queries
CREATE INDEX IF NOT EXISTS idx_pedido_items_producto_snapshot
    ON pedido_items
    USING GIN (producto_snapshot);

CREATE INDEX IF NOT EXISTS idx_sale_items_product_snapshot
    ON sale_items
    USING GIN (product_snapshot);

COMMIT;

