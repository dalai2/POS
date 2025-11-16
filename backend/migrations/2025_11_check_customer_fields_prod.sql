-- Diagnostic script to check if customer fields exist in ventas_contado
-- Run this in production to see current state

SELECT 'Checking customer fields in ventas_contado:' as status;

SELECT 
  column_name,
  data_type,
  is_nullable,
  CASE WHEN column_name IS NOT NULL THEN '✓ EXISTS' ELSE '✗ MISSING' END as field_status
FROM information_schema.columns 
WHERE table_name='ventas_contado' AND column_name IN ('customer_name', 'customer_phone', 'customer_address')
ORDER BY ordinal_position;

-- Show all columns in ventas_contado for reference
SELECT 'All columns in ventas_contado:' as info;

SELECT 
  ordinal_position,
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns 
WHERE table_name='ventas_contado'
ORDER BY ordinal_position;

