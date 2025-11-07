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

-- Agregar columna category si no existe
ALTER TABLE productos_pedido 
ADD COLUMN IF NOT EXISTS category VARCHAR(100);

-- Hacer que name sea NOT NULL (solo si todos los registros tienen valor)
-- IMPORTANTE: Primero actualiza los registros NULL si los hay:
UPDATE productos_pedido SET name = 'Sin nombre' WHERE name IS NULL;
ALTER TABLE productos_pedido ALTER COLUMN name SET NOT NULL;

-- Hacer que price sea NOT NULL con default 0
UPDATE productos_pedido SET price = 0 WHERE price IS NULL;
ALTER TABLE productos_pedido ALTER COLUMN price SET NOT NULL;
ALTER TABLE productos_pedido ALTER COLUMN price SET DEFAULT 0;

-- Hacer que cost_price sea NOT NULL con default 0
UPDATE productos_pedido SET cost_price = 0 WHERE cost_price IS NULL;
ALTER TABLE productos_pedido ALTER COLUMN cost_price SET NOT NULL;
ALTER TABLE productos_pedido ALTER COLUMN cost_price SET DEFAULT 0;

-- Agregar default true a disponible
ALTER TABLE productos_pedido ALTER COLUMN disponible SET DEFAULT true;
UPDATE productos_pedido SET disponible = true WHERE disponible IS NULL;

-- =====================================================
-- 2. NO SE CREARON NUEVAS TABLAS
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
-- 3. VERIFICACIONES (Opcional)
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


