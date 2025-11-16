-- Script para verificar y diagnosticar duplicados de folio_apartado
-- Ejecuta esto PRIMERO en producción para ver si hay problemas

-- ============================================================================
-- 1. BUSCAR FOLIOS DUPLICADOS
-- ============================================================================

SELECT 'SECTION 1: Folio Duplicates' as section;

SELECT 
  folio_apartado,
  COUNT(*) as count,
  STRING_AGG(id::text, ', ') as apartment_ids
FROM apartados
WHERE folio_apartado IS NOT NULL
GROUP BY folio_apartado
HAVING COUNT(*) > 1
ORDER BY count DESC;

-- ============================================================================
-- 2. VER TODOS LOS APARTADOS Y SUS FOLIOS
-- ============================================================================

SELECT 'SECTION 2: All Apartados with Folios' as section;

SELECT 
  id,
  folio_apartado,
  created_at,
  credit_status
FROM apartados
ORDER BY id;

-- ============================================================================
-- 3. BUSCAR GAPS EN LOS IDS (IDs faltantes)
-- ============================================================================

SELECT 'SECTION 3: ID Gaps' as section;

WITH id_sequence AS (
  SELECT generate_series(1, (SELECT MAX(id) FROM apartados)) as id
)
SELECT 
  id_sequence.id
FROM id_sequence
LEFT JOIN apartados ON id_sequence.id = apartados.id
WHERE apartados.id IS NULL
ORDER BY id_sequence.id;

-- ============================================================================
-- 4. VERIFICAR ESTADO DE LA SECUENCIA
-- ============================================================================

SELECT 'SECTION 4: Sequence Status' as section;

SELECT 
  'apartados_id_seq' as sequence_name,
  last_value as current_value,
  (SELECT MAX(id) FROM apartados) as max_apartment_id,
  CASE 
    WHEN last_value > (SELECT COALESCE(MAX(id), 0) FROM apartados) 
      THEN 'OK ✓'
    ELSE 'BEHIND - needs reset'
  END as status
FROM apartados_id_seq;

-- ============================================================================
-- 5. DUPLICATED FOLIOS DETAIL (si existen)
-- ============================================================================

SELECT 'SECTION 5: Detailed Duplicate Analysis' as section;

-- Ver cada folio duplicado con todos sus detalles
SELECT 
  a.id,
  a.folio_apartado,
  a.created_at,
  a.total,
  a.amount_paid,
  a.credit_status,
  COUNT(cp.id) as payment_count
FROM apartados a
LEFT JOIN credit_payments cp ON a.id = cp.apartado_id
WHERE a.folio_apartado IN (
  SELECT folio_apartado 
  FROM apartados 
  WHERE folio_apartado IS NOT NULL
  GROUP BY folio_apartado 
  HAVING COUNT(*) > 1
)
GROUP BY a.id, a.folio_apartado, a.created_at, a.total, a.amount_paid, a.credit_status
ORDER BY a.folio_apartado, a.id;

