-- CRITICAL FIX FOR PRODUCTION
-- Make payments.sale_id nullable to support new venta_contado_id linkage

BEGIN;

-- Check current state and make nullable
DO $$
DECLARE
    v_is_nullable TEXT;
BEGIN
    SELECT is_nullable INTO v_is_nullable 
    FROM information_schema.columns 
    WHERE table_name='payments' AND column_name='sale_id';
    
    IF v_is_nullable = 'NO' THEN
        RAISE NOTICE 'payments.sale_id is NOT NULL - fixing...';
        ALTER TABLE payments ALTER COLUMN sale_id DROP NOT NULL;
        RAISE NOTICE 'payments.sale_id is now NULLABLE ✓';
    ELSE
        RAISE NOTICE 'payments.sale_id is already NULLABLE ✓';
    END IF;
END$$;

-- Verify the change
SELECT 
  column_name,
  data_type,
  CASE WHEN is_nullable='YES' THEN 'NULLABLE ✓' ELSE 'NOT NULL ✗' END as status
FROM information_schema.columns 
WHERE table_name='payments' AND column_name IN ('sale_id', 'venta_contado_id')
ORDER BY ordinal_position;

COMMIT;

