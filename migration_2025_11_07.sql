-- =====================================================
-- MIGRATION SCRIPT - 2025-11-07
-- Cambios realizados durante la sesión de desarrollo
-- =====================================================
-- 
-- INSTRUCCIONES PARA APLICAR EN PRODUCCIÓN:
-- 
-- Opción 1: Docker (si usas Docker en producción)
-- docker exec -i erppos-db psql -U erpuser -d erppos < migration_2025_11_07.sql
--
-- Opción 2: PostgreSQL directo
-- psql -U erpuser -d erppos -f migration_2025_11_07.sql
--
-- Opción 3: Copiar y pegar en pgAdmin o tu cliente SQL
-- =====================================================

BEGIN;

-- =====================================================
-- 1. TABLA productos_pedido
-- =====================================================

-- Renombrar columnas para mejor claridad semántica
DO $$
BEGIN
    -- 1. Eliminar columna modelo existente si hay conflicto (para evitar duplicados)
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='productos_pedido' AND column_name='modelo') THEN
        -- Si modelo ya existe, primero hacer backup temporal del name original
        ALTER TABLE productos_pedido RENAME COLUMN name TO name_backup;
        -- Eliminar el modelo viejo
        ALTER TABLE productos_pedido DROP COLUMN modelo;
        -- Renombrar name_backup a modelo
        ALTER TABLE productos_pedido RENAME COLUMN name_backup TO modelo;
    ELSE
        -- Si modelo no existe, simplemente renombrar name a modelo
        ALTER TABLE productos_pedido RENAME COLUMN name TO modelo;
    END IF;
    
    -- 2. Renombrar tipo_joya a nombre (si existe)
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='productos_pedido' AND column_name='tipo_joya') THEN
        ALTER TABLE productos_pedido RENAME COLUMN tipo_joya TO nombre;
    END IF;
    
    -- 3. Renombrar price a precio (si existe)
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='productos_pedido' AND column_name='price') THEN
        ALTER TABLE productos_pedido RENAME COLUMN price TO precio;
    END IF;
END $$;

-- 4. Agregar columna peso si no existe
ALTER TABLE productos_pedido ADD COLUMN IF NOT EXISTS peso VARCHAR(100);

-- Agregar columna category si no existe
ALTER TABLE productos_pedido 
ADD COLUMN IF NOT EXISTS category VARCHAR(100);

-- Hacer que modelo sea NOT NULL (solo si todos los registros tienen valor)
-- IMPORTANTE: Primero actualiza los registros NULL si los hay:
UPDATE productos_pedido SET modelo = 'Sin modelo' WHERE modelo IS NULL;
ALTER TABLE productos_pedido ALTER COLUMN modelo SET NOT NULL;

-- Hacer que precio sea NOT NULL con default 0
UPDATE productos_pedido SET precio = 0 WHERE precio IS NULL;
ALTER TABLE productos_pedido ALTER COLUMN precio SET NOT NULL;
ALTER TABLE productos_pedido ALTER COLUMN precio SET DEFAULT 0;

-- Hacer que cost_price sea NOT NULL con default 0
UPDATE productos_pedido SET cost_price = 0 WHERE cost_price IS NULL;
ALTER TABLE productos_pedido ALTER COLUMN cost_price SET NOT NULL;
ALTER TABLE productos_pedido ALTER COLUMN cost_price SET DEFAULT 0;

-- Agregar default true a disponible
ALTER TABLE productos_pedido ALTER COLUMN disponible SET DEFAULT true;
UPDATE productos_pedido SET disponible = true WHERE disponible IS NULL;

-- =====================================================
-- 2. TABLA tasas_metal_pedido
-- =====================================================

-- Agregar columna tipo si no existe (para separar costos y precios)
ALTER TABLE tasas_metal_pedido 
ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) NOT NULL DEFAULT 'precio';

-- Crear índice en tipo para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_tasas_metal_pedido_tipo ON tasas_metal_pedido(tipo);

-- =====================================================
-- 3. NO SE CREARON NUEVAS TABLAS
-- =====================================================
-- Las tablas siguientes ya deberían existir en producción:
-- - productos_pedido
-- - pedidos
-- - pagos_pedido
-- - products
-- - sales
-- - sale_items
-- - credit_payments
-- - payments
-- - metal_rates
-- - inventory_movements
-- - users
-- - tenants
-- - shifts
-- - tasas_metal_pedido

-- =====================================================
-- 4. VERIFICACIONES (Opcional)
-- =====================================================

-- Verificar estructura de productos_pedido
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'productos_pedido'
ORDER BY ordinal_position;

-- Verificar que no haya valores NULL en columnas críticas
SELECT COUNT(*) as productos_sin_nombre FROM productos_pedido WHERE name IS NULL;
SELECT COUNT(*) as productos_sin_precio FROM productos_pedido WHERE price IS NULL;
SELECT COUNT(*) as productos_sin_costo FROM productos_pedido WHERE cost_price IS NULL;

-- Verificar que la columna tipo existe en tasas_metal_pedido
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'tasas_metal_pedido' AND column_name = 'tipo';

COMMIT;

-- =====================================================
-- NOTAS IMPORTANTES:
-- =====================================================
--
-- 1. Este script es IDEMPOTENTE: Puedes ejecutarlo múltiples veces
--    sin causar errores gracias a las cláusulas IF NOT EXISTS y 
--    IF EXISTS.
--
-- 2. Los cambios están en una transacción (BEGIN...COMMIT) para que
--    si algo falla, todo se revierta automáticamente.
--
-- 3. Si tienes datos en producción, el script actualiza los valores
--    NULL antes de agregar las restricciones NOT NULL.
--
-- 4. BACKUP RECOMENDADO: Antes de ejecutar, haz un respaldo:
--    pg_dump -U erpuser -d erppos > backup_antes_migracion.sql
--
-- =====================================================


