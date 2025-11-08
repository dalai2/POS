-- =====================================================
-- SCRIPT DE VERIFICACIÓN PRE-MIGRACIÓN
-- Ejecuta esto en PRODUCCIÓN para verificar qué cambios necesitas
-- =====================================================

-- 1. Verificar si la columna category existe en productos_pedido
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'productos_pedido' 
            AND column_name = 'category'
        ) 
        THEN 'Columna category YA EXISTE' 
        ELSE 'Columna category NO EXISTE - NECESITA MIGRACIÓN'
    END as status_category;

-- 2. Verificar estructura de name en productos_pedido
SELECT 
    column_name,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'productos_pedido' 
AND column_name = 'name';

-- 3. Verificar estructura de price en productos_pedido
SELECT 
    column_name,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'productos_pedido' 
AND column_name = 'price';

-- 4. Verificar estructura de cost_price en productos_pedido
SELECT 
    column_name,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'productos_pedido' 
AND column_name = 'cost_price';

-- 5. Verificar estructura de disponible en productos_pedido
SELECT 
    column_name,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'productos_pedido' 
AND column_name = 'disponible';

-- 6. Listar todas las tablas para verificar que existen
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- 7. Verificar si hay registros con valores NULL que causarían problemas
SELECT 
    'productos_pedido' as tabla,
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE name IS NULL) as name_null,
    COUNT(*) FILTER (WHERE price IS NULL) as price_null,
    COUNT(*) FILTER (WHERE cost_price IS NULL) as cost_price_null,
    COUNT(*) FILTER (WHERE disponible IS NULL) as disponible_null
FROM productos_pedido;

-- 8. Verificar si la columna tipo existe en tasas_metal_pedido
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'tasas_metal_pedido' 
            AND column_name = 'tipo'
        ) 
        THEN 'Columna tipo YA EXISTE' 
        ELSE 'Columna tipo NO EXISTE - NECESITA MIGRACIÓN'
    END as status_tipo_tasas;

-- =====================================================
-- RESULTADOS ESPERADOS:
-- =====================================================
-- 
-- Si todo está bien ANTES DE MIGRAR, deberías ver:
-- - category: "NO EXISTE - NECESITA MIGRACIÓN" (o "YA EXISTE")
-- - Columnas originales: name, tipo_joya, price
--
-- Si todo está bien DESPUÉS DE MIGRAR, deberías ver:
-- - category: "YA EXISTE"
-- - Columnas renombradas: nombre, name (antes tipo_joya), precio
-- - nombre: is_nullable = 'NO'
-- - precio: is_nullable = 'NO', column_default = 0
-- - cost_price: is_nullable = 'NO'
-- - disponible: column_default = 'true'
-- - tipo en tasas_metal_pedido: "YA EXISTE"
-- - Sin registros NULL que causen problemas
-- 
-- =====================================================


