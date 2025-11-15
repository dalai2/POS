-- ============================================
-- Migration: Add pedido_items table & relax pedidos.producto_pedido_id
-- ============================================

BEGIN;

-- 1. Create pedido_items table if it doesn't exist
CREATE TABLE IF NOT EXISTS pedido_items (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_pedido_id INTEGER REFERENCES productos_pedido(id) ON DELETE SET NULL,
    modelo VARCHAR(255),
    nombre VARCHAR(50),
    codigo VARCHAR(100),
    color VARCHAR(50),
    quilataje VARCHAR(20),
    base VARCHAR(50),
    talla VARCHAR(20),
    peso VARCHAR(100),
    peso_gramos NUMERIC(10, 3),
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario NUMERIC(10, 2) NOT NULL DEFAULT 0,
    total NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pedido_items_pedido_id ON pedido_items(pedido_id);
CREATE INDEX IF NOT EXISTS idx_pedido_items_producto_pedido_id ON pedido_items(producto_pedido_id);

-- 2. Make producto_pedido_id nullable for backwards compatibility
ALTER TABLE pedidos
    ALTER COLUMN producto_pedido_id DROP NOT NULL;

-- 3. Backfill existing pedidos into pedido_items (idempotent)
INSERT INTO pedido_items (
    pedido_id,
    producto_pedido_id,
    modelo,
    nombre,
    codigo,
    color,
    quilataje,
    base,
    talla,
    peso,
    peso_gramos,
    cantidad,
    precio_unitario,
    total,
    created_at,
    updated_at
)
SELECT
    p.id,
    p.producto_pedido_id,
    prod.modelo,
    prod.nombre,
    prod.codigo,
    prod.color,
    prod.quilataje,
    prod.base,
    prod.talla,
    prod.peso,
    prod.peso_gramos,
    p.cantidad,
    p.precio_unitario,
    p.total,
    p.created_at,
    p.updated_at
FROM pedidos p
LEFT JOIN productos_pedido prod ON prod.id = p.producto_pedido_id
WHERE NOT EXISTS (
    SELECT 1 FROM pedido_items it WHERE it.pedido_id = p.id
);

COMMIT;

