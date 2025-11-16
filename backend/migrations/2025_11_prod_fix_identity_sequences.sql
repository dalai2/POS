-- PRODUCTION FIX: Ensure id columns have proper GENERATED ALWAYS AS IDENTITY
-- This migration is for production to fix issues where items_venta_contado.id is NULL

BEGIN;

-- Check and fix items_venta_contado
DO $$
DECLARE
    v_current_default TEXT;
BEGIN
    -- Get current default for items_venta_contado.id
    SELECT column_default INTO v_current_default 
    FROM information_schema.columns 
    WHERE table_name='items_venta_contado' AND column_name='id';
    
    IF v_current_default IS NULL THEN
        -- No default set, add sequence
        CREATE SEQUENCE IF NOT EXISTS items_venta_contado_id_seq;
        ALTER TABLE items_venta_contado 
        ALTER COLUMN id SET DEFAULT nextval('items_venta_contado_id_seq'::regclass);
        ALTER SEQUENCE items_venta_contado_id_seq OWNED BY items_venta_contado.id;
        RAISE NOTICE 'Added sequence default to items_venta_contado.id';
    ELSE
        RAISE NOTICE 'items_venta_contado.id already has default: %', v_current_default;
    END IF;
END$$;

-- Check and fix items_apartado
DO $$
DECLARE
    v_current_default TEXT;
BEGIN
    SELECT column_default INTO v_current_default 
    FROM information_schema.columns 
    WHERE table_name='items_apartado' AND column_name='id';
    
    IF v_current_default IS NULL THEN
        CREATE SEQUENCE IF NOT EXISTS items_apartado_id_seq;
        ALTER TABLE items_apartado 
        ALTER COLUMN id SET DEFAULT nextval('items_apartado_id_seq'::regclass);
        ALTER SEQUENCE items_apartado_id_seq OWNED BY items_apartado.id;
        RAISE NOTICE 'Added sequence default to items_apartado.id';
    ELSE
        RAISE NOTICE 'items_apartado.id already has default: %', v_current_default;
    END IF;
END$$;

-- Verify sequences are set to correct values based on existing data
SELECT setval('items_venta_contado_id_seq', COALESCE((SELECT MAX(id) FROM items_venta_contado), 0) + 1);
SELECT setval('items_apartado_id_seq', COALESCE((SELECT MAX(id) FROM items_apartado), 0) + 1);

COMMIT;

