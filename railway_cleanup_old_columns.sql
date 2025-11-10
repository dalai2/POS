-- ============================================
-- SCRIPT PARA LIMPIAR COLUMNAS VIEJAS
-- Elimina las columnas antiguas si las nuevas ya existen
-- ============================================

DO $$ 
BEGIN
    -- Si 'modelo' existe y 'name' también existe, eliminar 'name'
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'modelo'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'name'
    ) THEN
        -- Primero copiar datos de name a modelo si modelo está vacío
        UPDATE productos_pedido SET modelo = name WHERE modelo IS NULL;
        
        -- Eliminar la columna name
        ALTER TABLE productos_pedido DROP COLUMN name;
        
        RAISE NOTICE '✅ Columna name eliminada exitosamente';
    ELSE
        RAISE NOTICE 'ℹ️ Columna name no necesita ser eliminada';
    END IF;

    -- Si 'nombre' existe y 'tipo_joya' también existe, eliminar 'tipo_joya'
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'nombre'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'tipo_joya'
    ) THEN
        -- Primero copiar datos de tipo_joya a nombre si nombre está vacío
        UPDATE productos_pedido SET nombre = tipo_joya WHERE nombre IS NULL;
        
        -- Eliminar la columna tipo_joya
        ALTER TABLE productos_pedido DROP COLUMN tipo_joya;
        
        RAISE NOTICE '✅ Columna tipo_joya eliminada exitosamente';
    ELSE
        RAISE NOTICE 'ℹ️ Columna tipo_joya no necesita ser eliminada';
    END IF;

    -- Si 'precio' existe y 'price' también existe, eliminar 'price'
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'precio'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'price'
    ) THEN
        -- Primero copiar datos de price a precio si precio está vacío
        UPDATE productos_pedido SET precio = price WHERE precio IS NULL;
        
        -- Eliminar la columna price
        ALTER TABLE productos_pedido DROP COLUMN price;
        
        RAISE NOTICE '✅ Columna price eliminada exitosamente';
    ELSE
        RAISE NOTICE 'ℹ️ Columna price no necesita ser eliminada';
    END IF;
END $$;

-- Verificar las columnas finales
SELECT '=== COLUMNAS FINALES DE PRODUCTOS_PEDIDO ===' as verificacion;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'productos_pedido' 
ORDER BY column_name;

