-- ============================================
-- SCRIPT DE SINCRONIZACIÓN COMPLETA RAILWAY
-- Ejecutar en orden para sincronizar la BD
-- ============================================

-- 1. Crear tabla tasas_metal_pedido si no existe
CREATE TABLE IF NOT EXISTS tasas_metal_pedido (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    metal_type VARCHAR(50) NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'precio',
    rate_per_gram NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasas_metal_pedido_tenant_id ON tasas_metal_pedido(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tasas_metal_pedido_metal_type ON tasas_metal_pedido(metal_type);
CREATE INDEX IF NOT EXISTS idx_tasas_metal_pedido_tipo ON tasas_metal_pedido(tipo);

-- 2. Actualizar productos_pedido - Renombrar columnas si existen con nombres viejos
DO $$ 
BEGIN
    -- Renombrar 'name' a 'modelo' solo si 'name' existe y 'modelo' NO existe
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'name'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'modelo'
    ) THEN
        ALTER TABLE productos_pedido RENAME COLUMN name TO modelo;
    END IF;

    -- Renombrar 'tipo_joya' a 'nombre' solo si 'tipo_joya' existe y 'nombre' NO existe
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'tipo_joya'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'nombre'
    ) THEN
        ALTER TABLE productos_pedido RENAME COLUMN tipo_joya TO nombre;
    END IF;

    -- Renombrar 'price' a 'precio' solo si 'price' existe y 'precio' NO existe
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'price'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'productos_pedido' AND column_name = 'precio'
    ) THEN
        ALTER TABLE productos_pedido RENAME COLUMN price TO precio;
    END IF;
END $$;

-- 3. Agregar columna 'peso' a productos_pedido si no existe
ALTER TABLE productos_pedido ADD COLUMN IF NOT EXISTS peso NUMERIC(10, 3);

-- 4. Verificar que pedidos tenga la columna 'estado' con los valores correctos
-- Los estados deben ser: pendiente, pedido, recibido, pagado, entregado, vencido, cancelado
-- (No hay cambio de esquema aquí, solo nota para verificación)

-- 5. Verificar que sales tenga las columnas necesarias
-- amount_paid, anticipo_pagado ya deben existir
-- (No hay cambio de esquema aquí, solo nota para verificación)

-- 6. Crear tabla status_history genérica si no existe
CREATE TABLE IF NOT EXISTS status_history (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(20) NOT NULL,
    entity_id INTEGER NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_email VARCHAR(255) NOT NULL,
    notes VARCHAR(500),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_status_history_tenant_id ON status_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_status_history_entity ON status_history(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_status_history_created_at ON status_history(created_at);

-- 7. Crear tabla productos_pedido_status_history si no existe
CREATE TABLE IF NOT EXISTS productos_pedido_status_history (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_productos_pedido_status_history_pedido_id 
    ON productos_pedido_status_history(pedido_id);
CREATE INDEX IF NOT EXISTS idx_productos_pedido_status_history_changed_at 
    ON productos_pedido_status_history(changed_at);

-- 8. Crear tabla credit_status_history si no existe (para apartados)
CREATE TABLE IF NOT EXISTS credit_status_history (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_credit_status_history_sale_id 
    ON credit_status_history(sale_id);
CREATE INDEX IF NOT EXISTS idx_credit_status_history_changed_at 
    ON credit_status_history(changed_at);

-- 9. Verificar índices importantes existen
CREATE INDEX IF NOT EXISTS idx_sales_tenant_created ON sales(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sales_tipo_venta ON sales(tipo_venta);
CREATE INDEX IF NOT EXISTS idx_sales_credit_status ON sales(credit_status);
CREATE INDEX IF NOT EXISTS idx_pedidos_tenant_created ON pedidos(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);
CREATE INDEX IF NOT EXISTS idx_payments_sale_id ON payments(sale_id);
CREATE INDEX IF NOT EXISTS idx_credit_payments_sale_id ON credit_payments(sale_id);
CREATE INDEX IF NOT EXISTS idx_pagos_pedido_pedido_id ON pagos_pedido(pedido_id);

-- 10. Verificar constraint de estado en pedidos (opcional, solo si necesitas validación a nivel DB)
-- ALTER TABLE pedidos DROP CONSTRAINT IF EXISTS pedidos_estado_check;
-- ALTER TABLE pedidos ADD CONSTRAINT pedidos_estado_check 
--     CHECK (estado IN ('pendiente', 'pedido', 'recibido', 'pagado', 'entregado', 'vencido', 'cancelado'));

-- ============================================
-- FIN DEL SCRIPT
-- ============================================

-- Para verificar que todo está correcto, ejecuta estas queries:
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'productos_pedido' ORDER BY column_name;
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tasas_metal_pedido' ORDER BY column_name;
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%status%';

