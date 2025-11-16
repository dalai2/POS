-- Fix product_snapshot for apartado #1 item #1

BEGIN;

SELECT '=== BEFORE: Apartado #1 items ===' as section;
SELECT id, apartado_id, product_id, quantity, product_snapshot 
FROM items_apartado WHERE apartado_id = 1;

-- Update item #1 with product snapshot
UPDATE items_apartado 
SET product_snapshot = jsonb_build_object(
  'id', 513,
  'codigo', 'S78',
  'nombre', 'MEDALLA-VIRGEN MILAGROSA-amarillo-10k oro_italiano-1.1g',
  'modelo', 'MEDALLA-VIRGEN MILAGROSA',
  'color', 'amarillo',
  'quilataje', '10k oro_italiano',
  'peso_gramos', 1.1,
  'description', 'MEDALLA-VIRGEN MILAGROSA-amarillo-10k oro_italiano-1.1g'
)
WHERE id = 1 AND apartado_id = 1;

SELECT '=== AFTER: Apartado #1 items ===' as section;
SELECT id, apartado_id, product_id, quantity, product_snapshot 
FROM items_apartado WHERE apartado_id = 1;

COMMIT;

