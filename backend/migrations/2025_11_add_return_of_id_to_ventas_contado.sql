-- Agregar campo return_of_id a ventas_contado para manejar devoluciones
-- Este campo referencia a la venta original cuando esta venta es una devolución

BEGIN;

-- Agregar columna return_of_id si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ventas_contado' AND column_name = 'return_of_id'
    ) THEN
        ALTER TABLE ventas_contado 
        ADD COLUMN return_of_id INTEGER NULL 
        REFERENCES ventas_contado(id) ON DELETE SET NULL;
        
        CREATE INDEX IF NOT EXISTS idx_ventas_contado_return_of_id 
        ON ventas_contado(return_of_id);
        
        RAISE NOTICE 'Columna return_of_id agregada a ventas_contado';
    ELSE
        RAISE NOTICE 'Columna return_of_id ya existe en ventas_contado';
    END IF;
END$$;

COMMIT;

