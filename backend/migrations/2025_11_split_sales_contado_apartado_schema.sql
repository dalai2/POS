-- Fase 1: Esquema para separar ventas de contado y apartados
-- Crear nuevas tablas y columnas necesarias sin tocar pedidos

BEGIN;

-- Tabla ventas_contado
CREATE TABLE IF NOT EXISTS ventas_contado (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    subtotal NUMERIC(10,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    tax_rate NUMERIC(5,2) NOT NULL DEFAULT 0,
    tax_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    total NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    vendedor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    utilidad NUMERIC(10,2) DEFAULT 0,
    total_cost NUMERIC(10,2) DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_ventas_contado_tenant ON ventas_contado(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ventas_contado_user ON ventas_contado(user_id);
CREATE INDEX IF NOT EXISTS idx_ventas_contado_vendedor ON ventas_contado(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_ventas_contado_created ON ventas_contado(created_at);

-- Tabla items_venta_contado
CREATE TABLE IF NOT EXISTS items_venta_contado (
    id INTEGER PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas_contado(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    codigo VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    product_snapshot JSONB
);

CREATE INDEX IF NOT EXISTS idx_items_venta_contado_venta ON items_venta_contado(venta_id);
CREATE INDEX IF NOT EXISTS idx_items_venta_contado_producto ON items_venta_contado(product_id);

-- Tabla apartados
CREATE TABLE IF NOT EXISTS apartados (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    subtotal NUMERIC(10,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    tax_rate NUMERIC(5,2) NOT NULL DEFAULT 0,
    tax_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    total NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    vendedor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    utilidad NUMERIC(10,2) DEFAULT 0,
    total_cost NUMERIC(10,2) DEFAULT 0,
    folio_apartado VARCHAR(50),
    customer_name VARCHAR(255),
    customer_phone VARCHAR(50),
    customer_address VARCHAR(500),
    amount_paid NUMERIC(10,2) DEFAULT 0,
    credit_status VARCHAR(20) DEFAULT 'pendiente'
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_apartados_folio ON apartados(folio_apartado);
CREATE INDEX IF NOT EXISTS idx_apartados_tenant ON apartados(tenant_id);
CREATE INDEX IF NOT EXISTS idx_apartados_vendedor ON apartados(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_apartados_created ON apartados(created_at);
CREATE INDEX IF NOT EXISTS idx_apartados_credit_status ON apartados(credit_status);

-- Tabla items_apartado
CREATE TABLE IF NOT EXISTS items_apartado (
    id INTEGER PRIMARY KEY,
    apartado_id INTEGER NOT NULL REFERENCES apartados(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    codigo VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    product_snapshot JSONB
);

CREATE INDEX IF NOT EXISTS idx_items_apartado_apartado ON items_apartado(apartado_id);
CREATE INDEX IF NOT EXISTS idx_items_apartado_producto ON items_apartado(product_id);

-- Extender payments para apuntar a ventas_contado
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='payments' AND column_name='venta_contado_id'
    ) THEN
        ALTER TABLE payments ADD COLUMN venta_contado_id INTEGER NULL REFERENCES ventas_contado(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_payments_venta_contado ON payments(venta_contado_id);
    END IF;
END$$;

-- Extender credit_payments para apuntar a apartados
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='credit_payments' AND column_name='apartado_id'
    ) THEN
        ALTER TABLE credit_payments ADD COLUMN apartado_id INTEGER NULL REFERENCES apartados(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_credit_payments_apartado ON credit_payments(apartado_id);
    END IF;
END$$;

COMMIT;


