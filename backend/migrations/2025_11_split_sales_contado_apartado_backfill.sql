-- Fase 2: Backfill de datos desde tablas legacy
-- Copiar sales/sale_items a nuevas tablas y mapear pagos

BEGIN;

-- Tabla temporal para mapear ids de sales -> ventas_contado/apartados
DROP TABLE IF EXISTS tmp_sales_map;
CREATE TEMP TABLE tmp_sales_map (
    sale_id INTEGER PRIMARY KEY,
    nueva_id INTEGER NOT NULL,
    tipo VARCHAR(20) NOT NULL -- 'contado' o 'credito'
);

-- Copiar ventas de contado
INSERT INTO ventas_contado (id, tenant_id, user_id, subtotal, discount_amount, tax_rate, tax_amount, total, created_at, vendedor_id, utilidad, total_cost)
SELECT s.id, s.tenant_id, s.user_id, s.subtotal, s.discount_amount, s.tax_rate, s.tax_amount, s.total, COALESCE(s.created_at, CURRENT_TIMESTAMP), s.vendedor_id, s.utilidad, s.total_cost
FROM sales s
WHERE (s.tipo_venta IS NULL OR s.tipo_venta = 'contado')
  AND s.return_of_id IS NULL;

-- Mapear ids de contado
INSERT INTO tmp_sales_map (sale_id, nueva_id, tipo)
SELECT s.id, s.id, 'contado'
FROM sales s
WHERE (s.tipo_venta IS NULL OR s.tipo_venta = 'contado')
  AND s.return_of_id IS NULL;

-- Copiar items de contado
INSERT INTO items_venta_contado (id, venta_id, product_id, name, codigo, quantity, unit_price, discount_pct, discount_amount, total_price, product_snapshot)
SELECT si.id, si.sale_id, si.product_id, si.name, si.codigo, si.quantity, si.unit_price, si.discount_pct, si.discount_amount, si.total_price, si.product_snapshot
FROM sale_items si
JOIN tmp_sales_map m ON m.sale_id = si.sale_id AND m.tipo = 'contado';

-- Copiar apartados (credito)
INSERT INTO apartados (id, tenant_id, user_id, subtotal, discount_amount, tax_rate, tax_amount, total, created_at, vendedor_id, utilidad, total_cost, folio_apartado, customer_name, customer_phone, customer_address, amount_paid, credit_status)
SELECT s.id, s.tenant_id, s.user_id, s.subtotal, s.discount_amount, s.tax_rate, s.tax_amount, s.total, COALESCE(s.created_at, CURRENT_TIMESTAMP), s.vendedor_id, s.utilidad, s.total_cost, s.folio_apartado, s.customer_name, s.customer_phone, s.customer_address, COALESCE(s.amount_paid, 0), COALESCE(s.credit_status, 'pendiente')
FROM sales s
WHERE s.tipo_venta = 'credito'
  AND s.return_of_id IS NULL;

-- Mapear ids de credito
INSERT INTO tmp_sales_map (sale_id, nueva_id, tipo)
SELECT s.id, s.id, 'credito'
FROM sales s
WHERE s.tipo_venta = 'credito'
  AND s.return_of_id IS NULL;

-- Copiar items de apartados
INSERT INTO items_apartado (id, apartado_id, product_id, name, codigo, quantity, unit_price, discount_pct, discount_amount, total_price, product_snapshot)
SELECT si.id, si.sale_id, si.product_id, si.name, si.codigo, si.quantity, si.unit_price, si.discount_pct, si.discount_amount, si.total_price, si.product_snapshot
FROM sale_items si
JOIN tmp_sales_map m ON m.sale_id = si.sale_id AND m.tipo = 'credito';

-- Backfill payments.venta_contado_id para ventas de contado
UPDATE payments p
SET venta_contado_id = m.nueva_id
FROM tmp_sales_map m
WHERE p.sale_id = m.sale_id AND m.tipo = 'contado';

-- Backfill credit_payments.apartado_id para apartados
UPDATE credit_payments cp
SET apartado_id = m.nueva_id
FROM tmp_sales_map m
WHERE cp.sale_id = m.sale_id AND m.tipo = 'credito';

COMMIT;


