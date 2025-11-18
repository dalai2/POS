-- Hacer sale_id nullable en credit_payments
-- Esto es necesario porque los nuevos apartados no usan sale_id (solo apartado_id)

BEGIN;

-- Hacer sale_id nullable en credit_payments
DO $$
BEGIN
    -- Verificar si sale_id es NOT NULL
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'credit_payments' 
        AND column_name = 'sale_id' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE credit_payments ALTER COLUMN sale_id DROP NOT NULL;
        RAISE NOTICE 'Columna sale_id en credit_payments ahora es nullable';
    ELSE
        RAISE NOTICE 'Columna sale_id en credit_payments ya es nullable';
    END IF;
END$$;

COMMIT;

