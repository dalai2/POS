-- ============================================
-- ACTUALIZAR FOLIOS EN TICKETS EXISTENTES
-- Solo actualiza el HTML, no elimina nada
-- ============================================

-- 1. Verificar ventas y sus folios actuales
SELECT '=== VENTAS Y SUS FOLIOS ACTUALES ===' as seccion;
SELECT
    id,
    folio_venta,
    customer_name as cliente
FROM ventas_contado
ORDER BY id ASC;

-- 2. Verificar tickets existentes antes de actualizar
SELECT '=== TICKETS ANTES DE ACTUALIZAR ===' as seccion;
SELECT
    t.id as ticket_id,
    t.venta_contado_id,
    v.folio_venta as folio_actual_venta,
    t.kind,
    CASE
        WHEN t.html LIKE '%V-000004%' THEN 'Tiene folio antiguo V-000004'
        WHEN t.html LIKE '%V-000005%' THEN 'Tiene folio antiguo V-000005'
        WHEN t.html LIKE '%V-000006%' THEN 'Tiene folio antiguo V-000006'
        WHEN t.html LIKE '%V-000007%' THEN 'Tiene folio antiguo V-000007'
        WHEN t.html LIKE '%V-000008%' THEN 'Tiene folio antiguo V-000008'
        ELSE 'Folio correcto o no encontrado'
    END as estado_folio
FROM tickets t
JOIN ventas_contado v ON t.venta_contado_id = v.id
WHERE t.venta_contado_id IS NOT NULL
ORDER BY t.venta_contado_id ASC;

-- 3. Actualizar HTML de tickets: reemplazar folios antiguos con los nuevos
-- Para cada venta, reemplazar su folio antiguo con el folio actual
UPDATE tickets t
SET html = REPLACE(t.html, 
    CASE t.venta_contado_id
        WHEN 1 THEN 'V-000004'
        WHEN 2 THEN 'V-000005'
        WHEN 3 THEN 'V-000006'
        WHEN 4 THEN 'V-000007'
        WHEN 5 THEN 'V-000008'
        ELSE NULL
    END,
    v.folio_venta
)
FROM ventas_contado v
WHERE t.venta_contado_id = v.id
AND t.venta_contado_id IN (1, 2, 3, 4, 5)
AND (
    (t.venta_contado_id = 1 AND t.html LIKE '%V-000004%') OR
    (t.venta_contado_id = 2 AND t.html LIKE '%V-000005%') OR
    (t.venta_contado_id = 3 AND t.html LIKE '%V-000006%') OR
    (t.venta_contado_id = 4 AND t.html LIKE '%V-000007%') OR
    (t.venta_contado_id = 5 AND t.html LIKE '%V-000008%')
);

-- 4. Verificar tickets después de actualizar
SELECT '=== TICKETS DESPUÉS DE ACTUALIZAR ===' as seccion;
SELECT
    t.id as ticket_id,
    t.venta_contado_id,
    v.folio_venta as folio_actual_venta,
    t.kind,
    CASE
        WHEN t.html LIKE '%' || v.folio_venta || '%' THEN 'Folio actualizado correctamente'
        ELSE 'Revisar manualmente'
    END as estado_folio
FROM tickets t
JOIN ventas_contado v ON t.venta_contado_id = v.id
WHERE t.venta_contado_id IS NOT NULL
ORDER BY t.venta_contado_id ASC;

-- 5. Resumen de actualización
SELECT '=== RESUMEN ===' as seccion;
SELECT
    COUNT(*) as total_tickets_verificados,
    'Los folios en los tickets HTML han sido actualizados' as mensaje
FROM tickets t
JOIN ventas_contado v ON t.venta_contado_id = v.id
WHERE t.venta_contado_id IS NOT NULL;
