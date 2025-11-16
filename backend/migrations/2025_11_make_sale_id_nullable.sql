-- Make sale_id nullable in payments table since we now use venta_contado_id
-- This allows payments to be linked to either legacy sales or new ventas_contado

BEGIN;

-- Alter payments table to make sale_id nullable
ALTER TABLE payments ALTER COLUMN sale_id DROP NOT NULL;

COMMIT;

