-- Verification script for production database schema
-- This script checks that all necessary migrations have been applied correctly
-- Run this to verify the state of your production database

\echo '=== SCHEMA VERIFICATION REPORT ==='
\echo ''

-- 1. Check if new tables exist
\echo '1. NEW TABLES EXISTENCE CHECK:'
\echo '   Checking ventas_contado...'
SELECT 
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='ventas_contado') 
    THEN '   ✓ ventas_contado EXISTS'
    ELSE '   ✗ ventas_contado MISSING'
  END;

\echo '   Checking items_venta_contado...'
SELECT 
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='items_venta_contado') 
    THEN '   ✓ items_venta_contado EXISTS'
    ELSE '   ✗ items_venta_contado MISSING'
  END;

\echo '   Checking apartados...'
SELECT 
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='apartados') 
    THEN '   ✓ apartados EXISTS'
    ELSE '   ✗ apartados MISSING'
  END;

\echo '   Checking items_apartado...'
SELECT 
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='items_apartado') 
    THEN '   ✓ items_apartado EXISTS'
    ELSE '   ✗ items_apartado MISSING'
  END;

\echo ''
\echo '2. COLUMN EXISTENCE CHECK IN NEW TABLES:'

\echo '   ventas_contado columns...'
SELECT 
  COUNT(*) as column_count,
  COUNT(*) FILTER (WHERE column_name IN ('id', 'tenant_id', 'user_id', 'subtotal', 'discount_amount', 'tax_rate', 'tax_amount', 'total', 'created_at', 'vendedor_id', 'utilidad', 'total_cost')) as required_count
FROM information_schema.columns 
WHERE table_name='ventas_contado';

\echo '   items_venta_contado columns...'
SELECT 
  COUNT(*) as column_count,
  COUNT(*) FILTER (WHERE column_name IN ('id', 'venta_id', 'product_id', 'name', 'codigo', 'quantity', 'unit_price', 'discount_pct', 'discount_amount', 'total_price', 'product_snapshot')) as required_count
FROM information_schema.columns 
WHERE table_name='items_venta_contado';

\echo '   apartados columns...'
SELECT 
  COUNT(*) as column_count,
  COUNT(*) FILTER (WHERE column_name IN ('id', 'tenant_id', 'user_id', 'subtotal', 'discount_amount', 'tax_rate', 'tax_amount', 'total', 'created_at', 'vendedor_id', 'utilidad', 'total_cost', 'folio_apartado', 'customer_name', 'customer_phone', 'customer_address', 'amount_paid', 'credit_status')) as required_count
FROM information_schema.columns 
WHERE table_name='apartados';

\echo '   items_apartado columns...'
SELECT 
  COUNT(*) as column_count,
  COUNT(*) FILTER (WHERE column_name IN ('id', 'apartado_id', 'product_id', 'name', 'codigo', 'quantity', 'unit_price', 'discount_pct', 'discount_amount', 'total_price', 'product_snapshot')) as required_count
FROM information_schema.columns 
WHERE table_name='items_apartado';

\echo ''
\echo '3. IDENTITY/SEQUENCE CHECK:'

\echo '   ventas_contado.id default...'
SELECT column_default FROM information_schema.columns 
WHERE table_name='ventas_contado' AND column_name='id';

\echo '   items_venta_contado.id default...'
SELECT column_default FROM information_schema.columns 
WHERE table_name='items_venta_contado' AND column_name='id';

\echo '   apartados.id default...'
SELECT column_default FROM information_schema.columns 
WHERE table_name='apartados' AND column_name='id';

\echo '   items_apartado.id default...'
SELECT column_default FROM information_schema.columns 
WHERE table_name='items_apartado' AND column_name='id';

\echo ''
\echo '4. PAYMENTS TABLE MODIFICATIONS:'

\echo '   payments.venta_contado_id column (should exist)...'
SELECT 
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='venta_contado_id') 
    THEN '   ✓ payments.venta_contado_id EXISTS'
    ELSE '   ✗ payments.venta_contado_id MISSING'
  END;

\echo '   payments.sale_id nullable (should allow NULL)...'
SELECT 
  is_nullable,
  CASE 
    WHEN is_nullable='YES' THEN '   ✓ payments.sale_id is NULLABLE'
    ELSE '   ✗ payments.sale_id is NOT NULL (NEEDS FIX)'
  END
FROM information_schema.columns 
WHERE table_name='payments' AND column_name='sale_id';

\echo ''
\echo '5. CREDIT_PAYMENTS TABLE MODIFICATIONS:'

\echo '   credit_payments.apartado_id column (should exist)...'
SELECT 
  CASE 
    WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='credit_payments' AND column_name='apartado_id') 
    THEN '   ✓ credit_payments.apartado_id EXISTS'
    ELSE '   ✗ credit_payments.apartado_id MISSING'
  END;

\echo '   credit_payments.sale_id nullable (should allow NULL)...'
SELECT 
  is_nullable,
  CASE 
    WHEN is_nullable='YES' THEN '   ✓ credit_payments.sale_id is NULLABLE'
    ELSE '   ✗ credit_payments.sale_id is NOT NULL (NEEDS FIX)'
  END
FROM information_schema.columns 
WHERE table_name='credit_payments' AND column_name='sale_id';

\echo ''
\echo '6. DATA SUMMARY:'

\echo '   ventas_contado count...'
SELECT COUNT(*) as count FROM ventas_contado;

\echo '   items_venta_contado count...'
SELECT COUNT(*) as count FROM items_venta_contado;

\echo '   apartados count...'
SELECT COUNT(*) as count FROM apartados;

\echo '   items_apartado count...'
SELECT COUNT(*) as count FROM items_apartado;

\echo '   payments with venta_contado_id...'
SELECT COUNT(*) as count FROM payments WHERE venta_contado_id IS NOT NULL;

\echo '   payments with sale_id (legacy)...'
SELECT COUNT(*) as count FROM payments WHERE sale_id IS NOT NULL;

\echo '   credit_payments with apartado_id...'
SELECT COUNT(*) as count FROM credit_payments WHERE apartado_id IS NOT NULL;

\echo '   credit_payments with sale_id (legacy)...'
SELECT COUNT(*) as count FROM credit_payments WHERE sale_id IS NOT NULL;

\echo ''
\echo '=== END OF VERIFICATION REPORT ==='

