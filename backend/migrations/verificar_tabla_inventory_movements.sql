-- Verificar que la tabla inventory_movements existe y tiene la estructura correcta
-- Ejecutar en psql o cualquier cliente SQL

-- Verificar si la tabla existe
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'inventory_movements'
);

-- Ver la estructura de la tabla
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'inventory_movements'
ORDER BY ordinal_position;

-- Ver todos los movimientos (si hay alguno)
SELECT COUNT(*) as total_movimientos FROM inventory_movements;

-- Ver los últimos 10 movimientos
SELECT 
    im.id,
    im.product_id,
    p.name as producto_nombre,
    p.codigo as producto_codigo,
    im.movement_type,
    im.quantity,
    im.cost,
    im.notes,
    im.created_at,
    u.email as usuario_email
FROM inventory_movements im
LEFT JOIN products p ON p.id = im.product_id
LEFT JOIN users u ON u.id = im.user_id
ORDER BY im.created_at DESC
LIMIT 10;

-- Verificar productos creados hoy con stock
SELECT 
    id,
    name,
    codigo,
    stock,
    created_at
FROM products
WHERE tenant_id = 1  -- Cambiar por tu tenant_id si es diferente
  AND created_at >= CURRENT_DATE
  AND (stock IS NOT NULL AND stock > 0)
ORDER BY created_at DESC;

