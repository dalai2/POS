-- Script para crear movimientos de inventario retroactivos para productos
-- que tienen stock pero no tienen movimientos registrados
-- 
-- IMPORTANTE: Este script crea movimientos de tipo "entrada" para productos
-- que tienen stock > 0 pero no tienen movimientos en inventory_movements
-- 
-- Ejecutar con cuidado y revisar los resultados antes de hacer commit

ROLLBACK;
BEGIN;

-- Verificar productos que tienen stock pero no tienen movimientos
SELECT 
    p.id,
    p.name,
    p.codigo,
    p.stock,
    p.created_at,
    COUNT(im.id) as movimientos_count
FROM products p
LEFT JOIN inventory_movements im ON im.product_id = p.id
WHERE p.tenant_id = 1  -- Cambiar por tu tenant_id si es diferente
  AND (p.stock IS NOT NULL AND p.stock > 0)
GROUP BY p.id, p.name, p.codigo, p.stock, p.created_at
HAVING COUNT(im.id) = 0
ORDER BY p.created_at DESC;

-- Crear movimientos retroactivos para productos con stock pero sin movimientos
-- Usar el usuario_id del primer usuario admin o el usuario que creó el producto
INSERT INTO inventory_movements (
    tenant_id,
    product_id,
    user_id,
    movement_type,
    quantity,
    cost,
    notes,
    created_at
)
SELECT 
    p.tenant_id,
    p.id as product_id,
    COALESCE(
        (SELECT id FROM users WHERE tenant_id = p.tenant_id AND role IN ('admin', 'owner') LIMIT 1),
        (SELECT id FROM users WHERE tenant_id = p.tenant_id LIMIT 1),
        1  -- Fallback a user_id = 1 si no hay usuarios
    ) as user_id,
    'entrada' as movement_type,
    p.stock as quantity,
    p.cost_price as cost,
    'Movimiento retroactivo: producto creado con stock inicial' as notes,
    COALESCE(p.created_at, CURRENT_TIMESTAMP) as created_at
FROM products p
WHERE p.tenant_id = 1  -- Cambiar por tu tenant_id si es diferente
  AND (p.stock IS NOT NULL AND p.stock > 0)
  AND NOT EXISTS (
      SELECT 1 FROM inventory_movements im 
      WHERE im.product_id = p.id
  );

-- Verificar los movimientos creados
SELECT 
    im.id,
    im.product_id,
    p.name as producto_nombre,
    p.codigo as producto_codigo,
    im.movement_type,
    im.quantity,
    im.cost,
    im.notes,
    im.created_at
FROM inventory_movements im
JOIN products p ON p.id = im.product_id
WHERE im.tenant_id = 1  -- Cambiar por tu tenant_id si es diferente
  AND im.notes LIKE '%retroactivo%'
ORDER BY im.created_at DESC;

-- Si todo se ve bien, hacer commit:
-- COMMIT;
-- Si hay problemas, hacer rollback:
-- ROLLBACK;

