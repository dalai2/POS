# Guía de Migración - Sistema de Historial de Estados

## ⚠️ IMPORTANTE
Esta migración crea una nueva tabla `status_history` para rastrear cambios de estado en ventas y pedidos.

## Pasos para Producción

### 1. Copiar el archivo de migración al servidor de base de datos
```bash
docker cp migration_status_history.sql erppos-db:/tmp/
```

### 2. Ejecutar la migración
```bash
docker exec erppos-db psql -U erpuser -d erppos -f /tmp/migration_status_history.sql
```

### 3. Verificar que la tabla se creó correctamente
La migración mostrará automáticamente la estructura de la tabla creada. Deberías ver:

```
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
   table_name   | column_name |          data_type          | is_nullable 
----------------+-------------+-----------------------------+-------------
 status_history | id          | integer                     | NO
 status_history | tenant_id   | integer                     | NO
 status_history | entity_type | character varying           | NO
 status_history | entity_id   | integer                     | NO
 status_history | old_status  | character varying           | YES
 status_history | new_status  | character varying           | NO
 status_history | user_id     | integer                     | NO
 status_history | user_email  | character varying           | NO
 status_history | notes       | character varying           | YES
 status_history | created_at  | timestamp without time zone | NO
```

### 4. Reiniciar el backend
```bash
docker restart erppos-backend
```

### 5. Verificar que el backend inició correctamente
```bash
docker logs erppos-backend --tail 20
```

Deberías ver:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## ¿Qué hace esta migración?

### Tabla `status_history`
Registra automáticamente:

1. **Cambios manuales de estado** (cuando admin/owner cambia el estado)
2. **Cambios automáticos por pagos** (pendiente → pagado, pendiente → entregado)
3. **Marcado como entregado** (pagado → entregado)

### Información guardada:
- **Fecha y hora** del cambio (con precisión de segundos)
- **Usuario** que hizo el cambio (ID y email)
- **Estado anterior y nuevo** (ejemplo: "pendiente" → "entregado")
- **Notas** automáticas describiendo el cambio
- **Tipo de entidad** ("sale" para ventas, "pedido" para pedidos)

## Funcionalidad Nueva

### Gestión de Abonos:
- ✅ Nuevo estado "**Entregado**" (diferente de "Pagado")
- ✅ Botón "Marcar entregado" para ventas pagadas
- ✅ Historial de estados visible en el modal de historial

### Gestión de Pedidos:
- ✅ Historial de estados visible en el modal de historial
- ✅ Registro automático al cambiar estado manualmente
- ✅ Registro automático al completar pagos

### Visualización:
El modal de "Historial" ahora muestra:
1. **Información del pedido/venta**
2. **Tabla de abonos/pagos**
3. **Historial de cambios de estado** (NUEVO) con:
   - Fecha (Ciudad de México)
   - Usuario que hizo el cambio
   - Cambio de estado (ej: "pendiente → pagado")
   - Notas explicativas

## Rollback (si es necesario)

Si necesitas revertir esta migración:

```sql
DROP TABLE IF EXISTS status_history CASCADE;
```

**NOTA**: Esto eliminará TODO el historial de cambios de estado registrado.

## Ejemplos de Registros

### Cambio manual de estado:
```
2025-11-08 14:30:00 | admin@andani.com | pendiente → confirmado | Estado cambiado manualmente de pendiente a confirmado
```

### Pago completo:
```
2025-11-08 15:45:00 | cajero@andani.com | pendiente → entregado | Pago de $5000.00 - Pedido completamente pagado
```

### Marcado como entregado:
```
2025-11-08 16:00:00 | admin@andani.com | pagado → entregado | Venta marcada como entregada
```

## Notas Importantes

- Los registros son **inmutables** (no se pueden editar ni eliminar desde la interfaz)
- El historial solo se muestra en el modal de "Historial" 
- Los pedidos/ventas existentes NO tendrán historial previo (solo cambios futuros)
- Para pruebas: Cambia el estado de un pedido manualmente y luego revisa el historial

