-- Migración: Agregar campos folio_apartado y folio_pedido
-- Fecha: 2025-11-11
-- Descripción: Agrega columnas para folios únicos de apartados y pedidos

-- ============================================
-- 1. AGREGAR COLUMNA folio_apartado A TABLA sales
-- ============================================
ALTER TABLE sales 
ADD COLUMN IF NOT EXISTS folio_apartado VARCHAR(50);

-- Crear índice para folio_apartado
CREATE INDEX IF NOT EXISTS ix_sales_folio_apartado 
ON sales (folio_apartado);

-- Generar folios para apartados existentes (ventas con tipo_venta = 'credito')
UPDATE sales 
SET folio_apartado = 'APT-' || LPAD(id::text, 6, '0')
WHERE tipo_venta = 'credito' 
AND folio_apartado IS NULL;

-- ============================================
-- 2. AGREGAR COLUMNA folio_pedido A TABLA pedidos
-- ============================================
ALTER TABLE pedidos 
ADD COLUMN IF NOT EXISTS folio_pedido VARCHAR(50);

-- Crear índice para folio_pedido
CREATE INDEX IF NOT EXISTS ix_pedidos_folio_pedido 
ON pedidos (folio_pedido);

-- Generar folios para pedidos existentes
UPDATE pedidos 
SET folio_pedido = 'PED-' || LPAD(id::text, 6, '0')
WHERE folio_pedido IS NULL;

-- ============================================
-- 3. VERIFICAR RESULTADOS
-- ============================================

-- Verificar apartados con folio
SELECT 
    COUNT(*) as total_apartados,
    COUNT(folio_apartado) as apartados_con_folio
FROM sales 
WHERE tipo_venta = 'credito';

-- Verificar pedidos con folio
SELECT 
    COUNT(*) as total_pedidos,
    COUNT(folio_pedido) as pedidos_con_folio
FROM pedidos;

-- Mostrar ejemplos de folios generados
SELECT id, folio_apartado, customer_name, total, created_at
FROM sales
WHERE tipo_venta = 'credito'
ORDER BY id DESC
LIMIT 5;

SELECT id, folio_pedido, cliente_nombre, total, created_at
FROM pedidos
ORDER BY id DESC
LIMIT 5;

-- ============================================
-- ROLLBACK (Si es necesario deshacer los cambios)
-- ============================================
-- DROP INDEX IF EXISTS ix_sales_folio_apartado;
-- ALTER TABLE sales DROP COLUMN IF EXISTS folio_apartado;
-- 
-- DROP INDEX IF EXISTS ix_pedidos_folio_pedido;
-- ALTER TABLE pedidos DROP COLUMN IF EXISTS folio_pedido;

