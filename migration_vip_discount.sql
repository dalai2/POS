-- Agregar columna descuento_vip_pct a apartados
ALTER TABLE apartados ADD COLUMN IF NOT EXISTS descuento_vip_pct NUMERIC(5, 2) DEFAULT 0;

-- Agregar columna descuento_vip_pct a ventas_contado
ALTER TABLE ventas_contado ADD COLUMN IF NOT EXISTS descuento_vip_pct NUMERIC(5, 2) DEFAULT 0;
