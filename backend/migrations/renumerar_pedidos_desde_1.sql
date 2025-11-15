-- ============================================
-- RENUMERAR PEDIDOS: Cambiar IDs a secuencia desde 1
-- Mantiene todos los datos, solo cambia los IDs
-- ============================================

-- Limpiar cualquier transacción abortada
ROLLBACK;

BEGIN;

-- 1. Mostrar estado actual
SELECT 'Estado ANTES de renumerar:' as info;
SELECT id, cliente_nombre, folio_pedido, created_at FROM pedidos ORDER BY id;

-- 2. Crear tabla temporal con el mapeo viejo ID -> nuevo ID
CREATE TEMP TABLE pedido_id_mapping (
    old_id INTEGER,
    new_id INTEGER,
    old_folio TEXT,
    new_folio TEXT,
    PRIMARY KEY (old_id)
);

-- 3. Poblar el mapeo con IDs y folios
INSERT INTO pedido_id_mapping (old_id, new_id, old_folio, new_folio)
SELECT 
    p.id as old_id,
    ROW_NUMBER() OVER (ORDER BY p.created_at, p.id) as new_id,
    p.folio_pedido as old_folio,
    'PED-' || LPAD((ROW_NUMBER() OVER (ORDER BY p.created_at, p.id))::text, 6, '0') as new_folio
FROM pedidos p;

-- Mostrar el mapeo
SELECT 'Mapeo de IDs y Folios:' as info;
SELECT * FROM pedido_id_mapping ORDER BY new_id;

-- 4. Deshabilitar temporalmente las restricciones de clave foránea
ALTER TABLE pagos_pedido DROP CONSTRAINT IF EXISTS pagos_pedido_pedido_id_fkey;
ALTER TABLE pedido_items DROP CONSTRAINT IF EXISTS pedido_items_pedido_id_fkey;

-- 5. Actualizar pagos_pedido con los nuevos IDs
UPDATE pagos_pedido pp
SET pedido_id = m.new_id
FROM pedido_id_mapping m
WHERE pp.pedido_id = m.old_id;

-- 6. Actualizar pedido_items con los nuevos IDs
UPDATE pedido_items pi
SET pedido_id = m.new_id
FROM pedido_id_mapping m
WHERE pi.pedido_id = m.old_id;

-- 6b. Actualizar status_history de pedidos con los nuevos IDs
UPDATE status_history sh
SET entity_id = m.new_id
FROM pedido_id_mapping m
WHERE sh.entity_type = 'pedido' AND sh.entity_id = m.old_id;

-- 7. Actualizar tickets: sale_id Y HTML (reemplazar folios)
DO $$
DECLARE
    mapping_rec RECORD;
BEGIN
    FOR mapping_rec IN SELECT * FROM pedido_id_mapping
    LOOP
        -- Actualizar el sale_id y reemplazar el folio en el HTML
        UPDATE tickets
        SET 
            sale_id = mapping_rec.new_id,
            html = REPLACE(html, mapping_rec.old_folio, mapping_rec.new_folio)
        WHERE sale_id = mapping_rec.old_id 
        AND (kind LIKE 'pedido%' OR kind = 'payment');
        
        RAISE NOTICE 'Ticket actualizado: Pedido % -> %, Folio % -> %', 
            mapping_rec.old_id, mapping_rec.new_id, 
            mapping_rec.old_folio, mapping_rec.new_folio;
    END LOOP;
END $$;

-- 8. Actualizar los IDs de pedidos directamente con UPDATE
-- Primero crear una copia de seguridad temporal con los datos originales
CREATE TEMP TABLE pedidos_backup AS
SELECT * FROM pedidos;

-- Actualizar cada pedido con su nuevo ID y folio
DO $$
DECLARE
    mapping_rec RECORD;
    backup_rec RECORD;
BEGIN
    -- Primero, actualizar todos los pedidos a IDs negativos temporales
    -- para evitar conflictos de clave primaria
    FOR mapping_rec IN SELECT * FROM pedido_id_mapping ORDER BY old_id
    LOOP
        UPDATE pedidos
        SET id = -mapping_rec.old_id
        WHERE id = mapping_rec.old_id;
    END LOOP;
    
    -- Ahora actualizar a los IDs nuevos finales
    FOR mapping_rec IN SELECT * FROM pedido_id_mapping ORDER BY new_id
    LOOP
        UPDATE pedidos
        SET 
            id = mapping_rec.new_id,
            folio_pedido = mapping_rec.new_folio
        WHERE id = -mapping_rec.old_id;
        
        RAISE NOTICE 'Pedido renumerado: ID % -> %, Folio % -> %', 
            mapping_rec.old_id, mapping_rec.new_id, 
            mapping_rec.old_folio, mapping_rec.new_folio;
    END LOOP;
END $$;

-- 9. Limpiar tabla de backup
DROP TABLE pedidos_backup;

-- 10. Volver a habilitar las restricciones
ALTER TABLE pagos_pedido 
ADD CONSTRAINT pagos_pedido_pedido_id_fkey 
FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE;

ALTER TABLE pedido_items 
ADD CONSTRAINT pedido_items_pedido_id_fkey 
FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE;

-- 11. Resetear la secuencia
SELECT setval('pedidos_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM pedidos), false);

-- 12. Verificar resultado
SELECT 'Estado DESPUÉS de renumerar:' as info;
SELECT id, cliente_nombre, folio_pedido, created_at FROM pedidos ORDER BY id;

SELECT 'Pagos actualizados:' as info;
SELECT id, pedido_id, monto, metodo_pago FROM pagos_pedido ORDER BY pedido_id;

SELECT 'Items actualizados:' as info;
SELECT id, pedido_id, modelo FROM pedido_items ORDER BY pedido_id;

SELECT 'Historial de estados actualizado:' as info;
SELECT id, entity_type, entity_id, old_status, new_status, user_email, created_at 
FROM status_history 
WHERE entity_type = 'pedido' 
ORDER BY entity_id, created_at;

SELECT 'Ejemplo de HTML actualizado en tickets:' as info;
SELECT 
    id, 
    sale_id, 
    kind,
    substring(html from 'FOLIO DE PEDIDO[^<]*') as folio_en_html
FROM tickets 
WHERE kind LIKE 'pedido%' OR kind = 'payment' 
ORDER BY sale_id
LIMIT 5;

SELECT 'Siguiente ID será:' as info, last_value FROM pedidos_id_seq;

COMMIT;

SELECT '✅ Renumeración completada con tickets actualizados' as resultado;

