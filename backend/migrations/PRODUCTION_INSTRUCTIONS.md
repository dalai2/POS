# Instrucciones para aplicar migraciones en PRODUCCIÓN

## ⚠️ IMPORTANTE: Leer antes de ejecutar

Esta migración corrige un problema donde los tickets de pedidos se guardaban con `sale_id` en lugar de `pedido_id`, causando que se mostraran tickets incorrectos cuando había colisiones de IDs entre pedidos y ventas.

## Prerequisitos

1. **BACKUP**: Hacer un backup completo de la base de datos de producción
2. **Staging**: Probar la migración en un ambiente de staging primero
3. **Acceso**: Tener acceso a la base de datos de producción con permisos de ALTER TABLE

## Archivos necesarios

- `PRODUCTION_add_pedido_id_to_tickets.sql` - Script de migración consolidado

## Pasos para aplicar en producción

### 1. Conectarse a la base de datos de producción

```bash
# Ajusta estos parámetros según tu configuración de producción
psql -U [usuario] -d [nombre_base_datos] -h [host]
```

### 2. Verificar el estado actual

Antes de ejecutar la migración, verifica cuántos tickets existen:

```sql
SELECT 
    COUNT(*) as total_tickets,
    COUNT(CASE WHEN kind LIKE 'pedido%' THEN 1 END) as pedido_tickets,
    COUNT(CASE WHEN kind IN ('payment', 'sale') THEN 1 END) as payment_tickets
FROM tickets;
```

### 3. Ejecutar la migración

```bash
# Desde la terminal, ejecuta el script:
psql -U [usuario] -d [nombre_base_datos] -h [host] -f PRODUCTION_add_pedido_id_to_tickets.sql
```

O desde psql:

```sql
\i /ruta/a/PRODUCTION_add_pedido_id_to_tickets.sql
```

### 4. Verificar los resultados

El script incluye reportes automáticos. Deberías ver:

- Número de tickets migrados
- Tipos de tickets (kinds) que se migraron
- Reporte de verificación con conteo de tickets por tipo

Ejemplo de salida esperada:
```
 tickets_migrated |       ticket_kinds        
------------------+---------------------------
                X | payment, pedido-payment-X
```

### 5. Verificación manual adicional

```sql
-- Ver tickets de pedidos migrados
SELECT t.id, t.sale_id, t.pedido_id, t.kind, p.tipo_pedido, p.total 
FROM tickets t 
LEFT JOIN pedidos p ON t.pedido_id = p.id 
WHERE t.pedido_id IS NOT NULL 
ORDER BY t.id;

-- Verificar que no haya tickets huérfanos
SELECT t.id, t.kind, t.pedido_id 
FROM tickets t 
WHERE t.pedido_id IS NOT NULL 
AND NOT EXISTS (SELECT 1 FROM pedidos p WHERE p.id = t.pedido_id);
```

### 6. Desplegar el código actualizado

Después de aplicar la migración de BD, debes desplegar las siguientes actualizaciones de código:

#### Backend:
- `backend/app/models/ticket.py` - Modelo actualizado con campo `pedido_id`
- `backend/app/routes/tickets.py` - Endpoints actualizados

#### Frontend:
- `frontend/src/utils/ticketGenerator.ts` - Función `saveTicket` actualizada
- `frontend/src/pages/PedidosPage.tsx` - Usa `pedidoId` al crear pedidos
- `frontend/src/pages/GestionPedidosPage.tsx` - Usa endpoint `/tickets/by-pedido/` y `pedidoId`

### 7. Reiniciar servicios

```bash
# Reiniciar el backend para que tome los cambios del modelo
# Ajusta según tu infraestructura de producción
systemctl restart [tu-servicio-backend]
# o
docker restart [tu-contenedor-backend]
```

## Rollback (si es necesario)

Si necesitas revertir la migración:

```sql
BEGIN;

-- Restaurar tickets de pedidos a sale_id
UPDATE tickets 
SET sale_id = pedido_id, pedido_id = NULL 
WHERE pedido_id IS NOT NULL;

-- Eliminar índices
DROP INDEX IF EXISTS ix_tickets_pedido_id;
DROP INDEX IF EXISTS uq_ticket_tenant_pedido_kind;

-- Restaurar constraint original
DROP INDEX IF EXISTS uq_ticket_tenant_sale_kind;
ALTER TABLE tickets 
ADD CONSTRAINT uq_ticket_tenant_sale_kind 
UNIQUE (tenant_id, sale_id, kind);

-- Eliminar columna
ALTER TABLE tickets DROP COLUMN IF EXISTS pedido_id;

COMMIT;
```

## Verificación post-despliegue

1. Crear un nuevo pedido de tipo "contado" y verificar que el ticket se guarde correctamente
2. Abrir el historial de un pedido existente y verificar que muestre el ticket correcto
3. Registrar un abono en un pedido apartado y verificar que el ticket se genere correctamente

## Preguntas frecuentes

**Q: ¿Puedo ejecutar la migración múltiples veces?**  
A: Sí, el script es idempotente. Usa `IF NOT EXISTS` para evitar errores.

**Q: ¿Afectará a los tickets de ventas existentes?**  
A: No, solo migra tickets que claramente pertenecen a pedidos.

**Q: ¿Qué pasa si hay un error durante la migración?**  
A: El script usa una transacción. Si falla, todo se revierte automáticamente.

**Q: ¿Cuánto tiempo toma la migración?**  
A: Depende del número de tickets. Para < 10,000 tickets, debería ser < 1 segundo.

## Soporte

Si encuentras problemas durante la migración, contacta al equipo de desarrollo con:
- Logs del error
- Resultados de las queries de verificación
- Número aproximado de tickets en la base de datos

