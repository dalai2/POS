-- DIAGNOSTIC SCRIPT - Run this FIRST in production to see what's wrong
-- This will tell you exactly what needs to be fixed

SELECT '=== PRODUCTION DIAGNOSIS ===' as title;

-- 1. Check payments.sale_id constraint
SELECT 'SECTION 1: payments.sale_id Nullable Status' as section;
SELECT 
  column_name,
  data_type,
  is_nullable,
  CASE 
    WHEN is_nullable='YES' THEN '✓ NULLABLE (OK)'
    ELSE '✗ NOT NULL (NEEDS FIX)'
  END as status
FROM information_schema.columns 
WHERE table_name='payments' AND column_name='sale_id';

-- 2. Check if venta_contado_id column exists
SELECT 'SECTION 2: payments.venta_contado_id Column' as section;
SELECT 
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='venta_contado_id')
    THEN '✓ Column EXISTS'
    ELSE '✗ Column MISSING'
  END as status,
  column_name,
  data_type
FROM information_schema.columns 
WHERE table_name='payments' AND column_name='venta_contado_id';

-- 3. Check if credit_payments.apartado_id column exists
SELECT 'SECTION 3: credit_payments.apartado_id Column' as section;
SELECT 
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='credit_payments' AND column_name='apartado_id')
    THEN '✓ Column EXISTS'
    ELSE '✗ Column MISSING'
  END as status,
  column_name,
  data_type
FROM information_schema.columns 
WHERE table_name='credit_payments' AND column_name='apartado_id';

-- 4. Check new table existence
SELECT 'SECTION 4: New Tables' as section;
SELECT 
  table_name,
  CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=t.table_name) THEN '✓ EXISTS' ELSE '✗ MISSING' END as status
FROM (
  SELECT 'ventas_contado' as table_name
  UNION ALL SELECT 'items_venta_contado'
  UNION ALL SELECT 'apartados'
  UNION ALL SELECT 'items_apartado'
) t;

-- 5. Check identity/sequences on id columns
SELECT 'SECTION 5: ID Column Auto-Increment' as section;
SELECT 
  table_name,
  column_name,
  CASE 
    WHEN column_default IS NOT NULL THEN '✓ HAS DEFAULT: ' || column_default
    ELSE '✗ NO DEFAULT'
  END as identity_status
FROM information_schema.columns 
WHERE table_name IN ('ventas_contado', 'items_venta_contado', 'apartados', 'items_apartado')
  AND column_name='id'
ORDER BY table_name;

-- 6. Check sequences exist and their current values
SELECT 'SECTION 6: Sequence Status' as section;
SELECT 
  sequence_name,
  CASE WHEN EXISTS (SELECT 1 FROM information_schema.sequences WHERE sequence_name=s.sequence_name) 
    THEN '✓ EXISTS' 
    ELSE '✗ MISSING' 
  END as exists_status
FROM (
  SELECT 'ventas_contado_id_seq' as sequence_name
  UNION ALL SELECT 'items_venta_contado_id_seq'
  UNION ALL SELECT 'apartados_id_seq'
  UNION ALL SELECT 'items_apartado_id_seq'
) s;

-- 7. Quick data counts
SELECT 'SECTION 7: Data Summary' as section;
SELECT 'ventas_contado' as table_name, COUNT(*) as count FROM ventas_contado
UNION ALL SELECT 'items_venta_contado', COUNT(*) FROM items_venta_contado
UNION ALL SELECT 'apartados', COUNT(*) FROM apartados
UNION ALL SELECT 'items_apartado', COUNT(*) FROM items_apartado
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'credit_payments', COUNT(*) FROM credit_payments;

-- 8. Check for orphaned records
SELECT 'SECTION 8: Orphaned Records Check' as section;
SELECT 
  'payments with invalid venta_contado_id' as check_type,
  COUNT(*) as orphan_count
FROM payments 
WHERE venta_contado_id IS NOT NULL 
  AND NOT EXISTS (SELECT 1 FROM ventas_contado WHERE ventas_contado.id = payments.venta_contado_id)
UNION ALL
SELECT 'credit_payments with invalid apartado_id', COUNT(*)
FROM credit_payments 
WHERE apartado_id IS NOT NULL 
  AND NOT EXISTS (SELECT 1 FROM apartados WHERE apartados.id = credit_payments.apartado_id);

