-- Agregar columnas de folio si no existen
-- Esta migración es necesaria antes de ejecutar la regeneración de IDs y folios

BEGIN;

-- Agregar folio_venta a ventas_contado si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='ventas_contado' AND column_name='folio_venta'
    ) THEN
        ALTER TABLE ventas_contado 
        ADD COLUMN folio_venta VARCHAR(50) NULL;
        
        CREATE INDEX IF NOT EXISTS idx_ventas_contado_folio_venta 
        ON ventas_contado(folio_venta);
        
        RAISE NOTICE 'Columna folio_venta agregada a ventas_contado';
    ELSE
        RAISE NOTICE 'Columna folio_venta ya existe en ventas_contado';
    END IF;
END$$;

-- Agregar folio_apartado a apartados si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='apartados' AND column_name='folio_apartado'
    ) THEN
        ALTER TABLE apartados 
        ADD COLUMN folio_apartado VARCHAR(50) NULL;
        
        CREATE INDEX IF NOT EXISTS idx_apartados_folio_apartado 
        ON apartados(folio_apartado);
        
        RAISE NOTICE 'Columna folio_apartado agregada a apartados';
    ELSE
        RAISE NOTICE 'Columna folio_apartado ya existe en apartados';
    END IF;
END$$;

-- Agregar folio_pedido a pedidos si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='pedidos' AND column_name='folio_pedido'
    ) THEN
        ALTER TABLE pedidos 
        ADD COLUMN folio_pedido VARCHAR(50) NULL;
        
        CREATE INDEX IF NOT EXISTS idx_pedidos_folio_pedido 
        ON pedidos(folio_pedido);
        
        RAISE NOTICE 'Columna folio_pedido agregada a pedidos';
    ELSE
        RAISE NOTICE 'Columna folio_pedido ya existe en pedidos';
    END IF;
END$$;

COMMIT;

