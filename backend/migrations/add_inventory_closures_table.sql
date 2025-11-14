-- Migration: Add inventory_closures table
-- Date: 2024-01-XX
-- Description: Creates the inventory_closures table for storing inventory snapshots/closures
--              Similar to cash_closures but for inventory control
-- 
-- IMPORTANT: Review and test this migration in a development environment before running in production
-- This migration is idempotent (safe to run multiple times)

-- Create inventory_closures table (matching structure of cash_closures)
CREATE TABLE IF NOT EXISTS inventory_closures (
    id SERIAL NOT NULL,
    tenant_id INTEGER NOT NULL,
    closure_date DATE NOT NULL,
    data JSON NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_inventory_closure_tenant_date UNIQUE (tenant_id, closure_date),
    FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

-- Create indexes for better query performance (only if they don't exist)
-- Note: PostgreSQL will automatically create indexes for PRIMARY KEY and UNIQUE constraints
-- These additional indexes may already be created by the UNIQUE constraint above
CREATE INDEX IF NOT EXISTS idx_inventory_closures_tenant_id 
    ON inventory_closures(tenant_id);

CREATE INDEX IF NOT EXISTS idx_inventory_closures_closure_date 
    ON inventory_closures(closure_date);

-- Add comment to table (PostgreSQL specific)
COMMENT ON TABLE inventory_closures IS 'Stores inventory control snapshots/closures for each day, similar to cash_closures but for inventory metrics';

