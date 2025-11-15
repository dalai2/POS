-- Consulta para verificar movimientos de inventario del día de hoy
-- Ejecutar en psql o cualquier cliente SQL

-- Ver todos los movimientos de inventario de hoy (fecha actual en zona horaria de México)
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
JOIN products p ON p.id = im.product_id
JOIN users u ON u.id = im.user_id
WHERE im.tenant_id = 1  -- Cambiar por tu tenant_id si es diferente
  AND im.created_at >= CURRENT_DATE  -- Movimientos desde inicio del día de hoy
  AND im.created_at < CURRENT_DATE + INTERVAL '1 day'  -- Hasta el final del día
ORDER BY im.created_at DESC;

-- Ver solo entradas (pulsos ingresados) de hoy
SELECT 
    im.id,
    im.product_id,
    p.name as producto_nombre,
    p.codigo as producto_codigo,
    im.quantity,
    im.cost,
    im.notes,
    im.created_at,
    u.email as usuario_email
FROM inventory_movements im
JOIN products p ON p.id = im.product_id
JOIN users u ON u.id = im.user_id
WHERE im.tenant_id = 1
  AND im.movement_type = 'entrada'
  AND im.created_at >= CURRENT_DATE
  AND im.created_at < CURRENT_DATE + INTERVAL '1 day'
ORDER BY im.created_at DESC;

-- Ver movimientos de un producto específico (reemplazar 'PULSO' con el nombre o código del producto)
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
JOIN products p ON p.id = im.product_id
JOIN users u ON u.id = im.user_id
WHERE im.tenant_id = 1
  AND (p.name ILIKE '%pulso%' OR p.codigo ILIKE '%pulso%')
  AND im.created_at >= CURRENT_DATE
ORDER BY im.created_at DESC;

