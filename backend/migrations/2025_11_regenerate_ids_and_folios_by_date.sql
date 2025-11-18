-- Regenerar IDs y folios por fecha de creación para apartados, ventas_contado y pedidos
-- Este script reconoce operaciones viejas y las migra correctamente
-- IMPORTANTE: Hacer backup completo de la base de datos antes de ejecutar
-- Safe to run in pgAdmin on production (wraps everything in a single transaction).

BEGIN;

-- ============================================================================
-- PARTE 1: REGENERAR IDs POR FECHA DE CREACIÓN
-- ============================================================================

-- 1.1) Drop FKs que referencian apartados, ventas_contado o pedidos
DO $$
DECLARE r record;
BEGIN
  FOR r IN (
    SELECT tc.table_schema, tc.table_name, tc.constraint_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu
      ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_name IN ('apartados','ventas_contado','pedidos')
  ) LOOP
    EXECUTE format('ALTER TABLE %I.%I DROP CONSTRAINT IF EXISTS %I', r.table_schema, r.table_name, r.constraint_name);
  END LOOP;
END$$;

-- 1.2) Crear tablas de mapeo ordenadas por fecha de creación
-- APARTADOS
DROP TABLE IF EXISTS tmp_map_apartado;
CREATE TEMP TABLE tmp_map_apartado AS
SELECT 
    id AS old_id, 
    tenant_id,
    ROW_NUMBER() OVER(PARTITION BY tenant_id ORDER BY created_at NULLS LAST, id) AS new_id
FROM apartados
ORDER BY tenant_id, created_at NULLS LAST, id;

-- VENTAS_CONTADO
DROP TABLE IF EXISTS tmp_map_contado;
CREATE TEMP TABLE tmp_map_contado AS
SELECT 
    id AS old_id, 
    tenant_id,
    ROW_NUMBER() OVER(PARTITION BY tenant_id ORDER BY created_at NULLS LAST, id) AS new_id
FROM ventas_contado
ORDER BY tenant_id, created_at NULLS LAST, id;

-- PEDIDOS
DROP TABLE IF EXISTS tmp_map_pedido;
CREATE TEMP TABLE tmp_map_pedido AS
SELECT 
    id AS old_id, 
    tenant_id,
    ROW_NUMBER() OVER(PARTITION BY tenant_id ORDER BY created_at NULLS LAST, id) AS new_id
FROM pedidos
ORDER BY tenant_id, created_at NULLS LAST, id;

-- 1.3) Actualizar IDs principales
UPDATE apartados a
SET id = m.new_id
FROM tmp_map_apartado m
WHERE a.id = m.old_id AND a.tenant_id = m.tenant_id;

UPDATE ventas_contado v
SET id = m.new_id
FROM tmp_map_contado m
WHERE v.id = m.old_id AND v.tenant_id = m.tenant_id;

UPDATE pedidos p
SET id = m.new_id
FROM tmp_map_pedido m
WHERE p.id = m.old_id AND p.tenant_id = m.tenant_id;

-- 1.4) Actualizar foreign keys de tablas relacionadas

-- APARTADOS: items_apartado
UPDATE items_apartado ia
SET apartado_id = m.new_id
FROM tmp_map_apartado m
WHERE ia.apartado_id = m.old_id;

-- APARTADOS: credit_payments (abonos)
UPDATE credit_payments cp
SET apartado_id = m.new_id
FROM tmp_map_apartado m
WHERE cp.apartado_id = m.old_id;

-- VENTAS_CONTADO: items_venta_contado
UPDATE items_venta_contado ivc
SET venta_id = m.new_id
FROM tmp_map_contado m
WHERE ivc.venta_id = m.old_id;

-- VENTAS_CONTADO: payments
UPDATE payments p
SET venta_contado_id = m.new_id
FROM tmp_map_contado m
WHERE p.venta_contado_id = m.old_id;

-- PEDIDOS: pedido_items
UPDATE pedido_items pi
SET pedido_id = m.new_id
FROM tmp_map_pedido m
WHERE pi.pedido_id = m.old_id;

-- PEDIDOS: pagos_pedido (abonos de pedidos)
UPDATE pagos_pedido pp
SET pedido_id = m.new_id
FROM tmp_map_pedido m
WHERE pp.pedido_id = m.old_id;

-- 1.5) Actualizar status_history
-- APARTADOS
UPDATE status_history sh
SET entity_id = m.new_id
FROM tmp_map_apartado m
WHERE sh.entity_type = 'apartado' AND sh.entity_id = m.old_id;

-- VENTAS_CONTADO (legacy: entity_type='sale' para ventas de contado antiguas)
UPDATE status_history sh
SET entity_id = m.new_id
FROM tmp_map_contado m
WHERE sh.entity_type = 'sale' AND sh.entity_id = m.old_id;

-- VENTAS_CONTADO (nuevo: entity_type='venta_contado')
UPDATE status_history sh
SET entity_id = m.new_id
FROM tmp_map_contado m
WHERE sh.entity_type = 'venta_contado' AND sh.entity_id = m.old_id;

-- PEDIDOS
UPDATE status_history sh
SET entity_id = m.new_id
FROM tmp_map_pedido m
WHERE sh.entity_type = 'pedido' AND sh.entity_id = m.old_id;

-- 1.6) Actualizar tickets (solo si las columnas existen)
-- APARTADOS
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tickets' AND column_name='apartado_id'
    ) THEN
        UPDATE tickets t
        SET apartado_id = m.new_id
        FROM tmp_map_apartado m
        WHERE t.apartado_id = m.old_id;
    END IF;
END$$;

-- VENTAS_CONTADO
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tickets' AND column_name='venta_contado_id'
    ) THEN
        UPDATE tickets t
        SET venta_contado_id = m.new_id
        FROM tmp_map_contado m
        WHERE t.venta_contado_id = m.old_id;
    END IF;
END$$;

-- PEDIDOS
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tickets' AND column_name='pedido_id'
    ) THEN
        UPDATE tickets t
        SET pedido_id = m.new_id
        FROM tmp_map_pedido m
        WHERE t.pedido_id = m.old_id;
    END IF;
END$$;

-- ============================================================================
-- PARTE 2: REGENERAR FOLIOS BASADOS EN NUEVOS IDs
-- ============================================================================

-- 2.1) Regenerar folios para APARTADOS
-- Formato: AP-TENANT_SLUG-000001
-- IMPORTANTE: Regenerar TODOS los folios basados en los nuevos IDs secuenciales
UPDATE apartados a
SET folio_apartado = (
    SELECT 
        'AP-' || UPPER(t.slug) || '-' || LPAD(a.id::text, 6, '0')
    FROM tenants t
    WHERE t.id = a.tenant_id
);

-- 2.2) Regenerar folios para VENTAS_CONTADO
-- Formato: V-TENANT_SLUG-000001
-- IMPORTANTE: Regenerar TODOS los folios basados en los nuevos IDs secuenciales
UPDATE ventas_contado v
SET folio_venta = (
    SELECT 
        'V-' || UPPER(t.slug) || '-' || LPAD(v.id::text, 6, '0')
    FROM tenants t
    WHERE t.id = v.tenant_id
);

-- 2.3) Regenerar folios para PEDIDOS
-- Formato: PED-TENANT_SLUG-000001
-- IMPORTANTE: Regenerar TODOS los folios basados en los nuevos IDs secuenciales
UPDATE pedidos p
SET folio_pedido = (
    SELECT 
        'PED-' || UPPER(t.slug) || '-' || LPAD(p.id::text, 6, '0')
    FROM tenants t
    WHERE t.id = p.tenant_id
);

-- ============================================================================
-- PARTE 3: ACTUALIZAR FOLIO_COUNTERS
-- ============================================================================

-- 3.1) Asegurar que existan contadores para cada tenant y tipo
INSERT INTO folio_counters (tenant_id, tipo, next_seq)
SELECT DISTINCT t.id, tipo.tipo, 1
FROM tenants t
CROSS JOIN (VALUES ('VENTA'), ('APARTADO'), ('PEDIDO')) AS tipo(tipo)
LEFT JOIN folio_counters fc ON fc.tenant_id = t.id AND fc.tipo = tipo.tipo
WHERE fc.id IS NULL;

-- 3.2) Actualizar next_seq basado en el máximo ID actual + 1
-- APARTADOS
UPDATE folio_counters fc
SET next_seq = COALESCE((
    SELECT MAX(id) + 1 
    FROM apartados a 
    WHERE a.tenant_id = fc.tenant_id
), 1)
WHERE fc.tipo = 'APARTADO';

-- VENTAS_CONTADO
UPDATE folio_counters fc
SET next_seq = COALESCE((
    SELECT MAX(id) + 1 
    FROM ventas_contado v 
    WHERE v.tenant_id = fc.tenant_id
), 1)
WHERE fc.tipo = 'VENTA';

-- PEDIDOS
UPDATE folio_counters fc
SET next_seq = COALESCE((
    SELECT MAX(id) + 1 
    FROM pedidos p 
    WHERE p.tenant_id = fc.tenant_id
), 1)
WHERE fc.tipo = 'PEDIDO';

-- ============================================================================
-- PARTE 4: RECREAR FOREIGN KEYS
-- ============================================================================

-- APARTADOS
ALTER TABLE items_apartado
  ADD CONSTRAINT items_apartado_apartado_id_fkey
  FOREIGN KEY (apartado_id) REFERENCES apartados(id) ON DELETE CASCADE;

ALTER TABLE credit_payments
  ADD CONSTRAINT credit_payments_apartado_id_fkey
  FOREIGN KEY (apartado_id) REFERENCES apartados(id) ON DELETE CASCADE;

ALTER TABLE tickets
  ADD CONSTRAINT tickets_apartado_id_fkey
  FOREIGN KEY (apartado_id) REFERENCES apartados(id) ON DELETE CASCADE;

-- VENTAS_CONTADO
ALTER TABLE items_venta_contado
  ADD CONSTRAINT items_venta_contado_venta_id_fkey
  FOREIGN KEY (venta_id) REFERENCES ventas_contado(id) ON DELETE CASCADE;

ALTER TABLE payments
  ADD CONSTRAINT payments_venta_contado_id_fkey
  FOREIGN KEY (venta_contado_id) REFERENCES ventas_contado(id) ON DELETE CASCADE;

ALTER TABLE tickets
  ADD CONSTRAINT tickets_venta_contado_id_fkey
  FOREIGN KEY (venta_contado_id) REFERENCES ventas_contado(id) ON DELETE CASCADE;

-- PEDIDOS
ALTER TABLE pedido_items
  ADD CONSTRAINT pedido_items_pedido_id_fkey
  FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE;

ALTER TABLE pagos_pedido
  ADD CONSTRAINT pagos_pedido_pedido_id_fkey
  FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE;

ALTER TABLE tickets
  ADD CONSTRAINT tickets_pedido_id_fkey
  FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE;

-- ============================================================================
-- PARTE 5: ASEGURAR SECUENCIAS DE IDENTITY
-- ============================================================================

-- 5.1) APARTADOS
DO $$
DECLARE next_apartado bigint;
DECLARE is_identity boolean;
BEGIN
  -- Verificar si la columna es IDENTITY
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'apartados' 
    AND column_name = 'id' 
    AND is_identity = 'YES'
  ) INTO is_identity;
  
  IF NOT is_identity THEN
    BEGIN
      EXECUTE 'ALTER TABLE apartados ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY';
    EXCEPTION WHEN others THEN
      NULL; -- Ignore if already identity/serial or can't convert
    END;
  END IF;
  
  -- Solo hacer RESTART si es IDENTITY
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'apartados' 
    AND column_name = 'id' 
    AND is_identity = 'YES'
  ) INTO is_identity;
  
  IF is_identity THEN
    SELECT COALESCE(MAX(id), 0) + 1 INTO next_apartado FROM apartados;
    EXECUTE format('ALTER TABLE apartados ALTER COLUMN id RESTART WITH %s', next_apartado);
  END IF;
END$$;

-- 5.2) VENTAS_CONTADO
DO $$
DECLARE next_contado bigint;
DECLARE is_identity boolean;
BEGIN
  -- Verificar si la columna es IDENTITY
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'ventas_contado' 
    AND column_name = 'id' 
    AND is_identity = 'YES'
  ) INTO is_identity;
  
  IF NOT is_identity THEN
    BEGIN
      EXECUTE 'ALTER TABLE ventas_contado ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY';
    EXCEPTION WHEN others THEN
      NULL; -- Ignore if already identity/serial or can't convert
    END;
  END IF;
  
  -- Solo hacer RESTART si es IDENTITY
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'ventas_contado' 
    AND column_name = 'id' 
    AND is_identity = 'YES'
  ) INTO is_identity;
  
  IF is_identity THEN
    SELECT COALESCE(MAX(id), 0) + 1 INTO next_contado FROM ventas_contado;
    EXECUTE format('ALTER TABLE ventas_contado ALTER COLUMN id RESTART WITH %s', next_contado);
  END IF;
END$$;

-- 5.3) PEDIDOS
DO $$
DECLARE next_pedido bigint;
DECLARE is_identity boolean;
BEGIN
  -- Verificar si la columna es IDENTITY
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'pedidos' 
    AND column_name = 'id' 
    AND is_identity = 'YES'
  ) INTO is_identity;
  
  IF NOT is_identity THEN
    BEGIN
      EXECUTE 'ALTER TABLE pedidos ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY';
    EXCEPTION WHEN others THEN
      NULL; -- Ignore if already identity/serial or can't convert
    END;
  END IF;
  
  -- Solo hacer RESTART si es IDENTITY
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'pedidos' 
    AND column_name = 'id' 
    AND is_identity = 'YES'
  ) INTO is_identity;
  
  IF is_identity THEN
    SELECT COALESCE(MAX(id), 0) + 1 INTO next_pedido FROM pedidos;
    EXECUTE format('ALTER TABLE pedidos ALTER COLUMN id RESTART WITH %s', next_pedido);
  END IF;
END$$;

COMMIT;

-- ============================================================================
-- VERIFICACIÓN POST-MIGRACIÓN (opcional, comentar para producción)
-- ============================================================================

-- Verificar que los IDs están ordenados por fecha
-- SELECT tenant_id, id, created_at, folio_apartado 
-- FROM apartados 
-- ORDER BY tenant_id, created_at, id 
-- LIMIT 10;

-- SELECT tenant_id, id, created_at, folio_venta 
-- FROM ventas_contado 
-- ORDER BY tenant_id, created_at, id 
-- LIMIT 10;

-- SELECT tenant_id, id, created_at, folio_pedido 
-- FROM pedidos 
-- ORDER BY tenant_id, created_at, id 
-- LIMIT 10;

