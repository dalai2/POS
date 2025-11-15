-- ============================================
-- Reset pedidos ID: Cambiar pedido ID 3 a 1
-- Versión corregida
-- ============================================

-- Primero hacer ROLLBACK si hay una transacción abortada
ROLLBACK;

-- Verificar estado actual
SELECT 'Estado actual - Pedidos:' as info;
SELECT id, cliente_nombre, created_at FROM pedidos ORDER BY id;

-- Verificar si existe pedido con ID 1
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pedidos WHERE id = 1) THEN
        RAISE NOTICE 'Ya existe un pedido con ID 1. Eliminándolo primero...';
        DELETE FROM pedido_items WHERE pedido_id = 1;
        DELETE FROM pagos_pedido WHERE pedido_id = 1;
        DELETE FROM pedidos WHERE id = 1;
    END IF;
END $$;

-- Crear el pedido con ID 1 (copiando del pedido 3)
INSERT INTO pedidos (
    id, tenant_id, producto_pedido_id, user_id, cliente_nombre, 
    cliente_telefono, cliente_email, cantidad, precio_unitario, total,
    folio_pedido, anticipo_pagado, saldo_pendiente, estado, tipo_pedido,
    fecha_entrega_estimada, fecha_entrega_real, notas_cliente, notas_internas,
    created_at, updated_at
)
SELECT 
    1, tenant_id, producto_pedido_id, user_id, cliente_nombre,
    cliente_telefono, cliente_email, cantidad, precio_unitario, total,
    folio_pedido, anticipo_pagado, saldo_pendiente, estado, tipo_pedido,
    fecha_entrega_estimada, fecha_entrega_real, notas_cliente, notas_internas,
    created_at, updated_at
FROM pedidos
WHERE id = 3;

-- Actualizar referencias en pedido_items
UPDATE pedido_items 
SET pedido_id = 1 
WHERE pedido_id = 3;

-- Actualizar referencias en pagos_pedido
UPDATE pagos_pedido 
SET pedido_id = 1 
WHERE pedido_id = 3;

-- Eliminar el pedido con ID 3
DELETE FROM pedidos WHERE id = 3;

-- Reiniciar la secuencia
SELECT setval('pedidos_id_seq', (SELECT COALESCE(MAX(id), 1) FROM pedidos));

-- Verificar resultado
SELECT 'Resultado final - Pedidos:' as info;
SELECT id, cliente_nombre, created_at FROM pedidos ORDER BY id;

SELECT 'Resultado final - Pagos:' as info;
SELECT id, pedido_id, monto FROM pagos_pedido ORDER BY pedido_id;

SELECT 'Resultado final - Items:' as info;
SELECT id, pedido_id, modelo FROM pedido_items ORDER BY pedido_id;
