# Instrucciones para diagnosticar y solucionar tickets incorrectos en Apartados

## Problema reportado

En "Gestión de Apartados" en producción, se están mostrando tickets incorrectos. El apartado muestra #10 pero querías que sea #1.

## Diagnóstico

### Paso 1: Ejecutar script de diagnóstico

```bash
psql -U [usuario] -d [base_datos] -h [host] -f PRODUCTION_diagnose_apartados_tickets.sql > diagnostico_apartados.txt
```

Este script te mostrará:
1. Todas las ventas a crédito con sus tickets
2. Tickets mal vinculados (sale_id apunta a ID inexistente)
3. **Colisiones de IDs** entre `sales` y `pedidos` (causa más probable)
4. Información específica del apartado #10
5. Estado de la secuencia de IDs

### Paso 2: Analizar el resultado

**Escenario A: Colisión de IDs**

Si encuentras que existe tanto:
- Una venta (sale) con ID 10 (apartado)
- Un pedido con ID 10

Entonces el problema es el mismo que con los pedidos: cuando cargas el apartado #10, el ticket puede estar vinculado al pedido #10 en lugar de la venta #10.

**Solución:** Aplicar la migración `PRODUCTION_add_pedido_id_to_tickets.sql` que separa los tickets de pedidos y ventas.

**Escenario B: Tickets huérfanos**

Si hay tickets con `sale_id` que no existe en la tabla `sales`, necesitas:
- Eliminar esos tickets huérfanos, O
- Reasignarlos al ID correcto

**Escenario C: Secuencia de IDs**

Si solo quieres resetear los IDs para que el próximo apartado sea #1 (sin afectar datos existentes):

```sql
-- Ver el ID máximo actual
SELECT MAX(id) FROM sales WHERE tipo_venta = 'credito';

-- Si quieres que el PRÓXIMO sea #1 (sin borrar datos existentes)
-- Esto solo funciona si no tienes ya una venta con ID 1
ALTER SEQUENCE sales_id_seq RESTART WITH 1;
```

## Soluciones

### Solución 1: Separar tickets de pedidos y ventas (Recomendado)

Si el problema es colisión de IDs:

1. Aplicar la migración principal:
```bash
psql -U [usuario] -d [base_datos] -h [host] -f PRODUCTION_add_pedido_id_to_tickets.sql
```

2. Desplegar código actualizado (backend + frontend)

3. Reiniciar servicios

### Solución 2: Resetear IDs de sales (DESTRUCTIVO - solo para desarrollo/staging)

⚠️ **SOLO SI QUIERES BORRAR TODAS LAS VENTAS Y EMPEZAR DE CERO**

```bash
# 1. BACKUP primero
pg_dump -U [usuario] -d [base_datos] -h [host] > backup_antes_reset.sql

# 2. Editar PRODUCTION_reset_sales_sequence.sql
# Remover los comentarios (--) de las líneas DELETE

# 3. Ejecutar
psql -U [usuario] -d [base_datos] -h [host] -f PRODUCTION_reset_sales_sequence.sql
```

### Solución 3: Resetear solo la secuencia (sin borrar datos)

Si solo quieres que el **próximo** apartado sea un número específico:

```sql
-- Para que el próximo sea #1
ALTER SEQUENCE sales_id_seq RESTART WITH 1;

-- Para que el próximo sea #50
ALTER SEQUENCE sales_id_seq RESTART WITH 50;

-- Para continuar desde el max ID actual + 1
SELECT setval('sales_id_seq', (SELECT MAX(id) FROM sales) + 1);
```

⚠️ **IMPORTANTE:** Resetear la secuencia a un número menor que el max ID existente causará errores de clave duplicada.

### Solución 4: Renumerar sales existentes (AVANZADO)

Si quieres renumerar todas las sales para que empiecen desde 1:

```sql
BEGIN;

-- 1. Crear tabla temporal con nuevos IDs
CREATE TEMP TABLE sales_renumber AS
SELECT 
    id as old_id,
    ROW_NUMBER() OVER (ORDER BY id) as new_id
FROM sales
WHERE tipo_venta = 'credito';

-- 2. Desactivar constraints temporalmente
ALTER TABLE sale_items DROP CONSTRAINT sale_items_sale_id_fkey;
ALTER TABLE tickets DROP CONSTRAINT tickets_sale_id_fkey;
ALTER TABLE credit_payments DROP CONSTRAINT credit_payments_sale_id_fkey;
ALTER TABLE status_history DROP CONSTRAINT status_history_entity_id_fkey;

-- 3. Actualizar IDs en orden inverso para evitar colisiones
UPDATE sales s
SET id = -r.new_id
FROM sales_renumber r
WHERE s.id = r.old_id;

-- 4. Actualizar referencias
UPDATE sale_items si
SET sale_id = -r.new_id
FROM sales_renumber r
WHERE si.sale_id = r.old_id;

UPDATE tickets t
SET sale_id = -r.new_id
FROM sales_renumber r
WHERE t.sale_id = r.old_id;

UPDATE credit_payments cp
SET sale_id = -r.new_id
FROM sales_renumber r
WHERE cp.sale_id = r.old_id;

UPDATE status_history sh
SET entity_id = -r.new_id
FROM sales_renumber r
WHERE sh.entity_type = 'sale' AND sh.entity_id = r.old_id;

-- 5. Cambiar a positivos
UPDATE sales SET id = -id WHERE id < 0;
UPDATE sale_items SET sale_id = -sale_id WHERE sale_id < 0;
UPDATE tickets SET sale_id = -sale_id WHERE sale_id < 0 AND sale_id IS NOT NULL;
UPDATE credit_payments SET sale_id = -sale_id WHERE sale_id < 0;
UPDATE status_history SET entity_id = -entity_id WHERE entity_type = 'sale' AND entity_id < 0;

-- 6. Restaurar constraints
ALTER TABLE sale_items ADD CONSTRAINT sale_items_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sales(id);
ALTER TABLE tickets ADD CONSTRAINT tickets_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sales(id);
ALTER TABLE credit_payments ADD CONSTRAINT credit_payments_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sales(id);

-- 7. Resetear secuencia
SELECT setval('sales_id_seq', (SELECT MAX(id) FROM sales) + 1);

-- Verificar
SELECT id, folio_apartado, customer_name FROM sales WHERE tipo_venta = 'credito' ORDER BY id LIMIT 10;

COMMIT;
-- Si algo sale mal: ROLLBACK;
```

## Recomendación

1. **Primero**: Ejecuta el script de diagnóstico para entender el problema exacto
2. **Si hay colisión de IDs**: Aplica `PRODUCTION_add_pedido_id_to_tickets.sql`
3. **Si solo quieres resetear la secuencia**: Usa la Solución 3
4. **Si quieres renumerar todo**: Usa la Solución 4 (requiere experiencia con SQL)

## Preguntas para aclarar

Antes de proceder, necesito saber:

1. ¿Cuántos apartados tienes actualmente en producción?
2. ¿Quieres mantener los datos existentes o empezar de cero?
3. ¿El problema es que el ticket muestra información incorrecta, o solo quieres que los IDs empiecen desde 1?
4. ¿Tienes apartados importantes que no puedes perder?

Ejecuta el script de diagnóstico y compárteme el resultado para darte una solución más precisa.

