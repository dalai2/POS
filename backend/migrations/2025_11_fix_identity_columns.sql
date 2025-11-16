-- Fix IDENTITY columns for ventas_contado, items_venta_contado, apartados, and items_apartado
-- These tables need IDENTITY to auto-generate IDs on INSERT

BEGIN;

-- For ventas_contado, add a SEQUENCE if it doesn't exist and recreate the column with IDENTITY
DO $$
BEGIN
    -- Create sequence for ventas_contado if not exists
    CREATE SEQUENCE IF NOT EXISTS ventas_contado_id_seq;
    
    -- Alter the id column to use the sequence
    ALTER TABLE ventas_contado 
    ALTER COLUMN id SET DEFAULT nextval('ventas_contado_id_seq'::regclass);
    
    -- Ensure the sequence is owned by the table
    ALTER SEQUENCE ventas_contado_id_seq OWNED BY ventas_contado.id;
EXCEPTION WHEN OTHERS THEN
    NULL; -- Ignore if already exists
END$$;

-- For items_venta_contado, add a SEQUENCE if it doesn't exist and recreate the column with IDENTITY
DO $$
BEGIN
    -- Create sequence for items_venta_contado if not exists
    CREATE SEQUENCE IF NOT EXISTS items_venta_contado_id_seq;
    
    -- Alter the id column to use the sequence
    ALTER TABLE items_venta_contado 
    ALTER COLUMN id SET DEFAULT nextval('items_venta_contado_id_seq'::regclass);
    
    -- Ensure the sequence is owned by the table
    ALTER SEQUENCE items_venta_contado_id_seq OWNED BY items_venta_contado.id;
EXCEPTION WHEN OTHERS THEN
    NULL; -- Ignore if already exists
END$$;

-- For apartados, add a SEQUENCE if it doesn't exist and recreate the column with IDENTITY
DO $$
BEGIN
    -- Create sequence for apartados if not exists
    CREATE SEQUENCE IF NOT EXISTS apartados_id_seq;
    
    -- Alter the id column to use the sequence
    ALTER TABLE apartados 
    ALTER COLUMN id SET DEFAULT nextval('apartados_id_seq'::regclass);
    
    -- Ensure the sequence is owned by the table
    ALTER SEQUENCE apartados_id_seq OWNED BY apartados.id;
EXCEPTION WHEN OTHERS THEN
    NULL; -- Ignore if already exists
END$$;

-- For items_apartado, add a SEQUENCE if it doesn't exist and recreate the column with IDENTITY
DO $$
BEGIN
    -- Create sequence for items_apartado if not exists
    CREATE SEQUENCE IF NOT EXISTS items_apartado_id_seq;
    
    -- Alter the id column to use the sequence
    ALTER TABLE items_apartado 
    ALTER COLUMN id SET DEFAULT nextval('items_apartado_id_seq'::regclass);
    
    -- Ensure the sequence is owned by the table
    ALTER SEQUENCE items_apartado_id_seq OWNED BY items_apartado.id;
EXCEPTION WHEN OTHERS THEN
    NULL; -- Ignore if already exists
END$$;

COMMIT;

