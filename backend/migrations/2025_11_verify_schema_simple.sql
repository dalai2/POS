-- Simplified verification script for production database schema
-- This version works in pgAdmin without \echo commands
-- Copy and paste the queries below into pgAdmin to verify each section

-- ============================================================================
-- 1. CHECK IF NEW TABLES EXIST
-- ============================================================================

-- Check ventas_contado
SELECT 
  'ventas_contado' as table_name,
  EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='ventas_contado') as exists
UNION ALL
-- Check items_venta_contado
SELECT 
  'items_venta_contado',
  EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='items_venta_contado')
UNION ALL
-- Check apartados
SELECT 
  'apartados',
  EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='apartados')
UNION ALL
-- Check items_apartado
SELECT 
  'items_apartado',
  EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='items_apartado');

-- ============================================================================
-- 2. CHECK IDENTITY/AUTO-INCREMENT ON ID COLUMNS
-- ============================================================================

SELECT 
  table_name,
  column_name,
  column_default,
  is_nullable
FROM information_schema.columns 
WHERE table_name IN ('ventas_contado', 'items_venta_contado', 'apartados', 'items_apartado')
  AND column_name='id'
ORDER BY table_name;

-- ============================================================================
-- 3. CHECK PAYMENTS TABLE MODIFICATIONS
-- ============================================================================

SELECT 
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns 
WHERE table_name='payments' AND column_name IN ('id', 'sale_id', 'venta_contado_id')
ORDER BY ordinal_position;

-- ============================================================================
-- 4. CHECK CREDIT_PAYMENTS TABLE MODIFICATIONS
-- ============================================================================

SELECT 
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns 
WHERE table_name='credit_payments' AND column_name IN ('id', 'sale_id', 'apartado_id')
ORDER BY ordinal_position;

-- ============================================================================
-- 5. CHECK FOREIGN KEY CONSTRAINTS
-- ============================================================================

SELECT
  constraint_name,
  table_name,
  column_name,
  referenced_table_name,
  referenced_column_name
FROM (
  SELECT
    c.constraint_name,
    c.table_name,
    kcu.column_name,
    ccu.table_name AS referenced_table_name,
    ccu.column_name AS referenced_column_name
  FROM information_schema.table_constraints c
  JOIN information_schema.key_column_usage kcu ON c.constraint_name = kcu.constraint_name
  JOIN information_schema.constraint_column_usage ccu ON c.constraint_name = ccu.constraint_name
  WHERE c.constraint_type = 'FOREIGN KEY'
    AND c.table_name IN ('ventas_contado', 'items_venta_contado', 'apartados', 'items_apartado', 'payments', 'credit_payments')
) AS fks
ORDER BY table_name, column_name;

-- ============================================================================
-- 6. DATA STATISTICS
-- ============================================================================

SELECT 'ventas_contado' as table_name, COUNT(*) as row_count FROM ventas_contado
UNION ALL
SELECT 'items_venta_contado', COUNT(*) FROM items_venta_contado
UNION ALL
SELECT 'apartados', COUNT(*) FROM apartados
UNION ALL
SELECT 'items_apartado', COUNT(*) FROM items_apartado
UNION ALL
SELECT 'payments (all)', COUNT(*) FROM payments
UNION ALL
SELECT 'payments (venta_contado_id)', COUNT(*) FROM payments WHERE venta_contado_id IS NOT NULL
UNION ALL
SELECT 'payments (legacy sale_id)', COUNT(*) FROM payments WHERE sale_id IS NOT NULL
UNION ALL
SELECT 'credit_payments (all)', COUNT(*) FROM credit_payments
UNION ALL
SELECT 'credit_payments (apartado_id)', COUNT(*) FROM credit_payments WHERE apartado_id IS NOT NULL
UNION ALL
SELECT 'credit_payments (legacy sale_id)', COUNT(*) FROM credit_payments WHERE sale_id IS NOT NULL;

-- ============================================================================
-- 7. VERIFY SEQUENCES ARE PROPERLY SET
-- ============================================================================

-- Check current sequence values
SELECT 'ventas_contado_id_seq' as seq_name, last_value FROM ventas_contado_id_seq
UNION ALL
SELECT 'items_venta_contado_id_seq', last_value FROM items_venta_contado_id_seq
UNION ALL
SELECT 'apartados_id_seq', last_value FROM apartados_id_seq
UNION ALL
SELECT 'items_apartado_id_seq', last_value FROM items_apartado_id_seq;

