-- PRODUCTION DATABASE VERIFICATION SCRIPT
-- Run this in pgAdmin to verify all migrations are applied correctly
-- This script has no psql-specific commands (\echo), it's pure SQL

-- ============================================================================
-- SECTION 1: TABLE EXISTENCE
-- ============================================================================
-- Expected result: 4 rows, all TRUE

SELECT 'Section 1: Table Existence' as section;

SELECT 
  'ventas_contado' as table_name,
  EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='ventas_contado') as exists
UNION ALL
SELECT 'items_venta_contado', EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='items_venta_contado')
UNION ALL
SELECT 'apartados', EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='apartados')
UNION ALL
SELECT 'items_apartado', EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='items_apartado');

-- ============================================================================
-- SECTION 2: IDENTITY COLUMNS (AUTO-INCREMENT)
-- ============================================================================
-- Expected result: All id columns should have a default value (sequence or GENERATED)

SELECT 'Section 2: Identity Columns' as section;

SELECT 
  table_name,
  column_name,
  CASE 
    WHEN column_default IS NOT NULL THEN 'HAS DEFAULT ✓'
    ELSE 'NO DEFAULT ✗ (NEEDS FIX)'
  END as status,
  column_default
FROM information_schema.columns 
WHERE table_name IN ('ventas_contado', 'items_venta_contado', 'apartados', 'items_apartado')
  AND column_name='id'
ORDER BY table_name;

-- ============================================================================
-- SECTION 3: PAYMENTS TABLE - NEW COLUMNS
-- ============================================================================
-- Expected: venta_contado_id should exist, sale_id should be nullable

SELECT 'Section 3: Payments Table Modifications' as section;

SELECT 
  column_name,
  data_type,
  CASE 
    WHEN is_nullable='YES' THEN 'NULLABLE ✓'
    ELSE 'NOT NULL'
  END as nullable_status,
  column_default
FROM information_schema.columns 
WHERE table_name='payments' AND column_name IN ('id', 'sale_id', 'venta_contado_id')
ORDER BY ordinal_position;

-- ============================================================================
-- SECTION 4: CREDIT_PAYMENTS TABLE - NEW COLUMNS
-- ============================================================================
-- Expected: apartado_id should exist, sale_id should be nullable

SELECT 'Section 4: Credit Payments Table Modifications' as section;

SELECT 
  column_name,
  data_type,
  CASE 
    WHEN is_nullable='YES' THEN 'NULLABLE ✓'
    ELSE 'NOT NULL'
  END as nullable_status,
  column_default
FROM information_schema.columns 
WHERE table_name='credit_payments' AND column_name IN ('id', 'sale_id', 'apartado_id')
ORDER BY ordinal_position;

-- ============================================================================
-- SECTION 5: FOREIGN KEY CONSTRAINTS
-- ============================================================================
-- Expected: All new FK relationships should exist (venta_contado, apartado, etc.)

SELECT 'Section 5: Foreign Key Constraints' as section;

SELECT
  c.table_name,
  kcu.column_name,
  ccu.table_name AS referenced_table_name,
  ccu.column_name AS referenced_column_name,
  c.constraint_name
FROM information_schema.table_constraints c
JOIN information_schema.key_column_usage kcu 
  ON c.constraint_name = kcu.constraint_name 
  AND c.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu 
  ON c.constraint_name = ccu.constraint_name 
  AND c.table_schema = ccu.table_schema
WHERE c.constraint_type = 'FOREIGN KEY'
  AND c.table_name IN ('ventas_contado', 'items_venta_contado', 'apartados', 'items_apartado', 'payments', 'credit_payments')
ORDER BY c.table_name, kcu.column_name;

-- ============================================================================
-- SECTION 6: SEQUENCE STATUS
-- ============================================================================
-- Expected: Sequences should exist for each table's id column

SELECT 'Section 6: Sequence Status' as section;

SELECT 
  sequence_name,
  CASE WHEN EXISTS (SELECT 1 FROM information_schema.sequences WHERE sequence_name=s.sequence_name) 
    THEN 'EXISTS ✓' 
    ELSE 'MISSING ✗'
  END as status
FROM (
  SELECT 'ventas_contado_id_seq' as sequence_name
  UNION ALL SELECT 'items_venta_contado_id_seq'
  UNION ALL SELECT 'apartados_id_seq'
  UNION ALL SELECT 'items_apartado_id_seq'
) s;

-- ============================================================================
-- SECTION 7: DATA COUNTS
-- ============================================================================
-- Summary of data in new tables and payment linkages

SELECT 'Section 7: Data Summary' as section;

SELECT 'ventas_contado' as entity, COUNT(*) as count FROM ventas_contado
UNION ALL
SELECT 'items_venta_contado', COUNT(*) FROM items_venta_contado
UNION ALL
SELECT 'apartados', COUNT(*) FROM apartados
UNION ALL
SELECT 'items_apartado', COUNT(*) FROM items_apartado
UNION ALL
SELECT 'payments (total)', COUNT(*) FROM payments
UNION ALL
SELECT 'payments (venta_contado_id linked)', COUNT(*) FROM payments WHERE venta_contado_id IS NOT NULL
UNION ALL
SELECT 'payments (legacy sale_id linked)', COUNT(*) FROM payments WHERE sale_id IS NOT NULL
UNION ALL
SELECT 'credit_payments (total)', COUNT(*) FROM credit_payments
UNION ALL
SELECT 'credit_payments (apartado_id linked)', COUNT(*) FROM credit_payments WHERE apartado_id IS NOT NULL
UNION ALL
SELECT 'credit_payments (legacy sale_id linked)', COUNT(*) FROM credit_payments WHERE sale_id IS NOT NULL;

-- ============================================================================
-- SECTION 8: QUICK HEALTH CHECK
-- ============================================================================
-- Check for any orphaned records or inconsistencies

SELECT 'Section 8: Health Check' as section;

-- Check for payments with venta_contado_id that don't exist
SELECT 'ORPHANED: payments with invalid venta_contado_id' as check_name, COUNT(*) as count
FROM payments p
WHERE p.venta_contado_id IS NOT NULL 
  AND NOT EXISTS (SELECT 1 FROM ventas_contado v WHERE v.id = p.venta_contado_id)
UNION ALL
-- Check for credit_payments with apartado_id that don't exist
SELECT 'ORPHANED: credit_payments with invalid apartado_id', COUNT(*)
FROM credit_payments cp
WHERE cp.apartado_id IS NOT NULL 
  AND NOT EXISTS (SELECT 1 FROM apartados a WHERE a.id = cp.apartado_id)
UNION ALL
-- Check for items_venta_contado with venta_id that don't exist
SELECT 'ORPHANED: items_venta_contado with invalid venta_id', COUNT(*)
FROM items_venta_contado iv
WHERE NOT EXISTS (SELECT 1 FROM ventas_contado v WHERE v.id = iv.venta_id)
UNION ALL
-- Check for items_apartado with apartado_id that don't exist
SELECT 'ORPHANED: items_apartado with invalid apartado_id', COUNT(*)
FROM items_apartado ia
WHERE NOT EXISTS (SELECT 1 FROM apartados a WHERE a.id = ia.apartado_id);

