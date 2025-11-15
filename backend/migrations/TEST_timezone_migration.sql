-- ============================================
-- Corrección de Timezone - EJECUCIÓN REAL
-- ============================================
-- Este script HACE cambios permanentes en la base de datos
-- Cada tabla se actualiza independientemente con manejo de errores
-- ============================================

-- Limpiar cualquier transacción bloqueada
ROLLBACK;

-- ============================================
-- VERIFICACIÓN PREVIA
-- ============================================
DO $$ BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'VERIFICACIÓN DE TABLAS (ANTES)';
    RAISE NOTICE '========================================';
END $$;

SELECT 'sales' as tabla, COUNT(*) as registros FROM sales
UNION ALL
SELECT 'pedidos', COUNT(*) FROM pedidos
UNION ALL
SELECT 'pagos_pedido', COUNT(*) FROM pagos_pedido
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'credit_payments', COUNT(*) FROM credit_payments
UNION ALL
SELECT 'inventory_movements', COUNT(*) FROM inventory_movements;

-- ============================================
-- 1. SALES (Ventas)
-- ============================================
DO $$ 
DECLARE
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '1. Actualizando SALES...';
    
    UPDATE sales
    SET created_at = created_at - INTERVAL '6 hours'
    WHERE created_at IS NOT NULL;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'SALES: % registros actualizados', affected_rows;
    RAISE NOTICE 'SALES: OK';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ERROR en SALES: %', SQLERRM;
END $$;

-- ============================================
-- 2. PEDIDOS
-- ============================================
DO $$ 
DECLARE
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '2. Actualizando PEDIDOS...';
    
    UPDATE pedidos
    SET 
        created_at = created_at - INTERVAL '6 hours',
        updated_at = CASE 
            WHEN updated_at IS NOT NULL THEN updated_at - INTERVAL '6 hours'
            ELSE NULL 
        END,
        fecha_entrega_real = CASE 
            WHEN fecha_entrega_real IS NOT NULL THEN fecha_entrega_real - INTERVAL '6 hours'
            ELSE NULL 
        END
    WHERE created_at IS NOT NULL;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'PEDIDOS: % registros actualizados', affected_rows;
    RAISE NOTICE 'PEDIDOS: OK';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ERROR en PEDIDOS: %', SQLERRM;
END $$;

-- ============================================
-- 3. PAGOS DE PEDIDOS
-- ============================================
DO $$ 
DECLARE
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '3. Actualizando PAGOS_PEDIDO...';
    
    UPDATE pagos_pedido
    SET created_at = created_at - INTERVAL '6 hours'
    WHERE created_at IS NOT NULL;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'PAGOS_PEDIDO: % registros actualizados', affected_rows;
    RAISE NOTICE 'PAGOS_PEDIDO: OK';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ERROR en PAGOS_PEDIDO: %', SQLERRM;
END $$;

-- ============================================
-- 4. PAYMENTS (Verificar si existe created_at)
-- ============================================
DO $$ 
DECLARE
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '4. Verificando PAYMENTS...';
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'payments' 
        AND column_name = 'created_at'
    ) THEN
        UPDATE payments
        SET created_at = created_at - INTERVAL '6 hours'
        WHERE created_at IS NOT NULL;
        
        GET DIAGNOSTICS affected_rows = ROW_COUNT;
        RAISE NOTICE 'PAYMENTS: % registros actualizados', affected_rows;
    ELSE
        RAISE NOTICE 'PAYMENTS: NO tiene columna created_at, saltando...';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ERROR en PAYMENTS: %', SQLERRM;
END $$;

-- ============================================
-- 5. CREDIT_PAYMENTS (Abonos)
-- ============================================
DO $$ 
DECLARE
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '5. Actualizando CREDIT_PAYMENTS...';
    
    UPDATE credit_payments
    SET created_at = created_at - INTERVAL '6 hours'
    WHERE created_at IS NOT NULL;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'CREDIT_PAYMENTS: % registros actualizados', affected_rows;
    RAISE NOTICE 'CREDIT_PAYMENTS: OK';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ERROR en CREDIT_PAYMENTS: %', SQLERRM;
END $$;

-- ============================================
-- 6. INVENTORY_MOVEMENTS
-- ============================================
DO $$ 
DECLARE
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '6. Actualizando INVENTORY_MOVEMENTS...';
    
    UPDATE inventory_movements
    SET created_at = created_at - INTERVAL '6 hours'
    WHERE created_at IS NOT NULL;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'INVENTORY_MOVEMENTS: % registros actualizados', affected_rows;
    RAISE NOTICE 'INVENTORY_MOVEMENTS: OK';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ERROR en INVENTORY_MOVEMENTS: %', SQLERRM;
END $$;

-- ============================================
-- 7. PRODUCTOS_PEDIDO (Verificar columnas)
-- ============================================
DO $$ 
DECLARE
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '7. Verificando PRODUCTOS_PEDIDO...';
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' 
        AND column_name = 'created_at'
    ) THEN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'productos_pedido' 
            AND column_name = 'updated_at'
        ) THEN
            UPDATE productos_pedido
            SET 
                created_at = created_at - INTERVAL '6 hours',
                updated_at = CASE 
                    WHEN updated_at IS NOT NULL THEN updated_at - INTERVAL '6 hours'
                    ELSE NULL 
                END
            WHERE created_at IS NOT NULL;
        ELSE
            UPDATE productos_pedido
            SET created_at = created_at - INTERVAL '6 hours'
            WHERE created_at IS NOT NULL;
        END IF;
        
        GET DIAGNOSTICS affected_rows = ROW_COUNT;
        RAISE NOTICE 'PRODUCTOS_PEDIDO: % registros actualizados', affected_rows;
    ELSE
        RAISE NOTICE 'PRODUCTOS_PEDIDO: NO tiene columna created_at, saltando...';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ERROR en PRODUCTOS_PEDIDO: %', SQLERRM;
END $$;

-- ============================================
-- 8. PRODUCTS (Verificar si existe created_at)
-- ============================================
DO $$ 
DECLARE
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '8. Verificando PRODUCTS...';
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name = 'created_at'
    ) THEN
        UPDATE products
        SET created_at = created_at - INTERVAL '6 hours'
        WHERE created_at IS NOT NULL;
        
        GET DIAGNOSTICS affected_rows = ROW_COUNT;
        RAISE NOTICE 'PRODUCTS: % registros actualizados', affected_rows;
    ELSE
        RAISE NOTICE 'PRODUCTS: NO tiene columna created_at, saltando...';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ERROR en PRODUCTS: %', SQLERRM;
END $$;

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================
DO $$ BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'VERIFICACIÓN FINAL (DESPUÉS)';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Distribución de ventas por día (últimos 15 días):';
END $$;

SELECT 
    DATE(created_at) as fecha,
    COUNT(*) as num_ventas,
    SUM(total) as total_vendido
FROM sales
GROUP BY DATE(created_at)
ORDER BY DATE(created_at) DESC
LIMIT 15;

DO $$ BEGIN RAISE NOTICE 'Últimas 10 ventas:'; END $$;

SELECT 
    id,
    created_at,
    total,
    tipo_venta
FROM sales
ORDER BY created_at DESC
LIMIT 10;

DO $$ BEGIN RAISE NOTICE 'Últimos 10 pedidos:'; END $$;

SELECT 
    id,
    created_at,
    cliente_nombre,
    estado,
    total
FROM pedidos
ORDER BY created_at DESC
LIMIT 10;

-- ============================================
-- CONFIRMAR CAMBIOS
-- ============================================
DO $$ BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRACIÓN COMPLETADA';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Todos los cambios han sido aplicados.';
    RAISE NOTICE 'Las fechas ahora están en hora México.';
END $$;

-- Confirmar todos los cambios
COMMIT;
