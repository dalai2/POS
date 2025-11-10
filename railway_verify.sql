-- ============================================
-- SCRIPT DE VERIFICACIÓN RAILWAY
-- Ejecutar DESPUÉS del script de sincronización
-- ============================================

-- 1. Verificar que tasas_metal_pedido existe
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasas_metal_pedido')
    THEN '✅ tasas_metal_pedido existe'
    ELSE '❌ tasas_metal_pedido NO existe'
    END as status;

-- 2. Verificar columnas de productos_pedido
SELECT '=== PRODUCTOS_PEDIDO ===' as seccion;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'productos_pedido' 
ORDER BY column_name;

-- 3. Verificar que las columnas renombradas existen
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'productos_pedido' AND column_name = 'modelo')
    THEN '✅ columna modelo existe'
    ELSE '❌ columna modelo NO existe (debería haberse renombrado de name)'
    END as status
UNION ALL
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'productos_pedido' AND column_name = 'nombre')
    THEN '✅ columna nombre existe'
    ELSE '❌ columna nombre NO existe (debería haberse renombrado de tipo_joya)'
    END
UNION ALL
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'productos_pedido' AND column_name = 'precio')
    THEN '✅ columna precio existe'
    ELSE '❌ columna precio NO existe (debería haberse renombrado de price)'
    END
UNION ALL
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'productos_pedido' AND column_name = 'peso')
    THEN '✅ columna peso existe'
    ELSE '❌ columna peso NO existe (debería haberse agregado)'
    END;

-- 4. Verificar tablas de historial
SELECT '=== TABLAS DE HISTORIAL ===' as seccion;
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'status_history')
    THEN '✅ status_history existe'
    ELSE '❌ status_history NO existe'
    END as status
UNION ALL
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'productos_pedido_status_history')
    THEN '✅ productos_pedido_status_history existe'
    ELSE '❌ productos_pedido_status_history NO existe'
    END
UNION ALL
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'credit_status_history')
    THEN '✅ credit_status_history existe'
    ELSE '❌ credit_status_history NO existe'
    END;

-- 5. Verificar índices importantes
SELECT '=== ÍNDICES ===' as seccion;
SELECT 
    schemaname, 
    tablename, 
    indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND (
        tablename IN ('tasas_metal_pedido', 'productos_pedido', 'pedidos', 'sales')
        OR tablename LIKE '%status_history%'
    )
ORDER BY tablename, indexname;

-- 6. Contar registros en tablas principales
SELECT '=== CONTEO DE REGISTROS ===' as seccion;
SELECT 'sales' as tabla, COUNT(*) as total FROM sales
UNION ALL
SELECT 'pedidos', COUNT(*) FROM pedidos
UNION ALL
SELECT 'productos_pedido', COUNT(*) FROM productos_pedido
UNION ALL
SELECT 'tasas_metal_pedido', COUNT(*) FROM tasas_metal_pedido
UNION ALL
SELECT 'status_history', COUNT(*) FROM status_history
UNION ALL
SELECT 'productos_pedido_status_history', COUNT(*) FROM productos_pedido_status_history
UNION ALL
SELECT 'credit_status_history', COUNT(*) FROM credit_status_history;

-- 7. Verificar que NO existan las columnas viejas
SELECT '=== VERIFICAR COLUMNAS VIEJAS ELIMINADAS ===' as seccion;
SELECT 
    CASE WHEN NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'productos_pedido' AND column_name = 'name')
    THEN '✅ columna name NO existe (correcto, fue renombrada a modelo)'
    ELSE '⚠️ columna name AÚN existe (debes renombrarla manualmente)'
    END as status
UNION ALL
SELECT 
    CASE WHEN NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'productos_pedido' AND column_name = 'tipo_joya')
    THEN '✅ columna tipo_joya NO existe (correcto, fue renombrada a nombre)'
    ELSE '⚠️ columna tipo_joya AÚN existe (debes renombrarla manualmente)'
    END
UNION ALL
SELECT 
    CASE WHEN NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'productos_pedido' AND column_name = 'price')
    THEN '✅ columna price NO existe (correcto, fue renombrada a precio)'
    ELSE '⚠️ columna price AÚN existe (debes renombrarla manualmente)'
    END;

-- ============================================
-- Si todos los checks muestran ✅, todo está sincronizado correctamente
-- ============================================

