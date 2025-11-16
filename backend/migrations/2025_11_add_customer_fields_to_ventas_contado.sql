-- Add customer fields to ventas_contado for better ticket information

BEGIN;

-- Add customer fields to ventas_contado if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='ventas_contado' AND column_name='customer_name'
    ) THEN
        ALTER TABLE ventas_contado ADD COLUMN customer_name VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='ventas_contado' AND column_name='customer_phone'
    ) THEN
        ALTER TABLE ventas_contado ADD COLUMN customer_phone VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='ventas_contado' AND column_name='customer_address'
    ) THEN
        ALTER TABLE ventas_contado ADD COLUMN customer_address VARCHAR(500);
    END IF;
END$$;

COMMIT;

