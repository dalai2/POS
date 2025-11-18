-- Crear tabla customers con ID único y agrupación por teléfono
-- Mismo teléfono = mismo cliente

BEGIN;

-- Crear tabla customers
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_customers_tenant_id ON customers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);

-- Crear constraint único: mismo teléfono en el mismo tenant = mismo cliente
CREATE UNIQUE INDEX IF NOT EXISTS uq_customers_tenant_phone 
    ON customers(tenant_id, phone) 
    WHERE phone IS NOT NULL;

-- Migrar datos existentes de ventas_contado
INSERT INTO customers (tenant_id, name, phone, created_at)
SELECT DISTINCT ON (vc.tenant_id, COALESCE(vc.customer_phone, ''))
    vc.tenant_id,
    COALESCE(vc.customer_name, 'Cliente Sin Nombre'),
    vc.customer_phone,
    MIN(vc.created_at) as created_at
FROM ventas_contado vc
WHERE vc.customer_name IS NOT NULL 
    AND vc.customer_name != ''
    AND (vc.customer_phone IS NOT NULL OR vc.customer_name IS NOT NULL)
GROUP BY vc.tenant_id, vc.customer_phone, vc.customer_name
ON CONFLICT (tenant_id, phone) WHERE phone IS NOT NULL DO NOTHING;

-- Migrar datos existentes de apartados
INSERT INTO customers (tenant_id, name, phone, created_at)
SELECT DISTINCT ON (a.tenant_id, COALESCE(a.customer_phone, ''))
    a.tenant_id,
    COALESCE(a.customer_name, 'Cliente Sin Nombre'),
    a.customer_phone,
    MIN(a.created_at) as created_at
FROM apartados a
WHERE a.customer_name IS NOT NULL 
    AND a.customer_name != ''
    AND (a.customer_phone IS NOT NULL OR a.customer_name IS NOT NULL)
GROUP BY a.tenant_id, a.customer_phone, a.customer_name
ON CONFLICT (tenant_id, phone) WHERE phone IS NOT NULL DO NOTHING;

-- Migrar datos existentes de pedidos
INSERT INTO customers (tenant_id, name, phone, created_at)
SELECT DISTINCT ON (p.tenant_id, COALESCE(p.cliente_telefono, ''))
    p.tenant_id,
    COALESCE(p.cliente_nombre, 'Cliente Sin Nombre'),
    p.cliente_telefono,
    MIN(p.created_at) as created_at
FROM pedidos p
WHERE p.cliente_nombre IS NOT NULL 
    AND p.cliente_nombre != ''
    AND (p.cliente_telefono IS NOT NULL OR p.cliente_nombre IS NOT NULL)
GROUP BY p.tenant_id, p.cliente_telefono, p.cliente_nombre
ON CONFLICT (tenant_id, phone) WHERE phone IS NOT NULL DO NOTHING;

-- Para clientes sin teléfono, crear registros únicos por nombre (solo si no hay teléfono)
-- Esto maneja casos donde el mismo nombre aparece sin teléfono
INSERT INTO customers (tenant_id, name, phone, created_at)
SELECT DISTINCT ON (vc.tenant_id, vc.customer_name)
    vc.tenant_id,
    vc.customer_name,
    NULL as phone,
    MIN(vc.created_at) as created_at
FROM ventas_contado vc
WHERE vc.customer_name IS NOT NULL 
    AND vc.customer_name != ''
    AND vc.customer_phone IS NULL
    AND NOT EXISTS (
        SELECT 1 FROM customers c 
        WHERE c.tenant_id = vc.tenant_id 
        AND c.name = vc.customer_name 
        AND c.phone IS NULL
    )
GROUP BY vc.tenant_id, vc.customer_name
ON CONFLICT DO NOTHING;

COMMIT;

