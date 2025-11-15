-- Script para borrar las últimas 691 entradas de productos_pedido
-- Ordenadas por id descendente (las más recientes primero)

ROLLBACK; -- Cambiar a COMMIT; después de revisar

BEGIN;

-- Verificar cuántos registros hay antes de borrar
DO $$
DECLARE
    total_count INTEGER;
    ids_to_delete INTEGER[];
BEGIN
    -- Contar total de registros
    SELECT COUNT(*) INTO total_count FROM productos_pedido;
    RAISE NOTICE 'Total de registros antes de borrar: %', total_count;
    
    -- Obtener los IDs de las últimas 691 entradas (ordenadas por id descendente)
    SELECT ARRAY_AGG(id ORDER BY id DESC)
    INTO ids_to_delete
    FROM (
        SELECT id 
        FROM productos_pedido 
        ORDER BY id DESC 
        LIMIT 691
    ) sub;
    
    -- Verificar que hay suficientes registros
    IF array_length(ids_to_delete, 1) IS NULL THEN
        RAISE NOTICE 'No hay suficientes registros para borrar';
    ELSE
        RAISE NOTICE 'Se borrarán % registros', array_length(ids_to_delete, 1);
        
        -- Borrar los registros
        DELETE FROM productos_pedido 
        WHERE id = ANY(ids_to_delete);
        
        RAISE NOTICE 'Registros borrados exitosamente';
    END IF;
END $$;

-- Verificar cuántos registros quedan después de borrar
SELECT COUNT(*) as total_registros_restantes FROM productos_pedido;

-- Mostrar los últimos 10 registros que quedan (para verificación)
SELECT id, modelo, nombre, codigo, created_at 
FROM productos_pedido 
ORDER BY id DESC 
LIMIT 10;

-- COMMIT; -- Descomentar para aplicar los cambios permanentemente
-- ROLLBACK; -- Descomentar para revertir los cambios

