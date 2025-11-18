-- Agregar columnas faltantes a tickets si no existen
-- Esta migración es necesaria antes de ejecutar la regeneración de IDs y folios

BEGIN;

-- Agregar venta_contado_id si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tickets' AND column_name='venta_contado_id'
    ) THEN
        ALTER TABLE tickets 
        ADD COLUMN venta_contado_id INTEGER NULL REFERENCES ventas_contado(id) ON DELETE CASCADE;
        
        CREATE INDEX IF NOT EXISTS idx_tickets_venta_contado_id 
        ON tickets(venta_contado_id);
        
        RAISE NOTICE 'Columna venta_contado_id agregada a tickets';
    ELSE
        RAISE NOTICE 'Columna venta_contado_id ya existe en tickets';
    END IF;
END$$;

-- Agregar apartado_id si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tickets' AND column_name='apartado_id'
    ) THEN
        ALTER TABLE tickets 
        ADD COLUMN apartado_id INTEGER NULL REFERENCES apartados(id) ON DELETE CASCADE;
        
        CREATE INDEX IF NOT EXISTS idx_tickets_apartado_id 
        ON tickets(apartado_id);
        
        RAISE NOTICE 'Columna apartado_id agregada a tickets';
    ELSE
        RAISE NOTICE 'Columna apartado_id ya existe en tickets';
    END IF;
END$$;

-- Agregar pedido_id si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tickets' AND column_name='pedido_id'
    ) THEN
        ALTER TABLE tickets 
        ADD COLUMN pedido_id INTEGER NULL REFERENCES pedidos(id) ON DELETE CASCADE;
        
        CREATE INDEX IF NOT EXISTS idx_tickets_pedido_id 
        ON tickets(pedido_id);
        
        RAISE NOTICE 'Columna pedido_id agregada a tickets';
    ELSE
        RAISE NOTICE 'Columna pedido_id ya existe en tickets';
    END IF;
END$$;

COMMIT;

