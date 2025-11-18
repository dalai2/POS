-- Agregar columna apartado_id a credit_payments si no existe
-- Esta migración es necesaria para que los pagos de apartados funcionen correctamente

BEGIN;

-- Agregar columna apartado_id si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='credit_payments' AND column_name='apartado_id'
    ) THEN
        ALTER TABLE credit_payments 
        ADD COLUMN apartado_id INTEGER NULL REFERENCES apartados(id) ON DELETE CASCADE;
        
        CREATE INDEX IF NOT EXISTS idx_credit_payments_apartado 
        ON credit_payments(apartado_id);
        
        RAISE NOTICE 'Columna apartado_id agregada a credit_payments';
    ELSE
        RAISE NOTICE 'Columna apartado_id ya existe en credit_payments';
    END IF;
END$$;

COMMIT;

