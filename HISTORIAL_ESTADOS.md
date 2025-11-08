# Historial de Estados - Sistema de Auditoría

## Descripción
Sistema robusto de auditoría que registra automáticamente todos los cambios de estado en ventas a crédito y pedidos.

## Tabla de Base de Datos

### `status_history`
```sql
- id (SERIAL PRIMARY KEY)
- tenant_id (INTEGER, FK → tenants)
- entity_type (VARCHAR(20)) - "sale" o "pedido"
- entity_id (INTEGER) - ID de la venta o pedido
- old_status (VARCHAR(50), nullable) - Estado anterior
- new_status (VARCHAR(50)) - Nuevo estado
- user_id (INTEGER, FK → users) - Usuario que hizo el cambio
- user_email (VARCHAR(255)) - Email del usuario (guardado por si se elimina)
- notes (VARCHAR(500), nullable) - Notas sobre el cambio
- created_at (TIMESTAMP) - Fecha y hora del cambio
```

## Cambios de Estado Registrados

### Ventas a Crédito (`entity_type = "sale"`):
1. **pendiente → pagado**: Cuando se completa el pago total
   - Se registra automáticamente cuando `amount_paid >= total`
   - Nota incluye el monto del último abono

2. **pagado → entregado**: Cuando se marca manualmente como entregado
   - Se registra al hacer clic en "Marcar entregado"
   - Nota: "Venta marcada como entregada"

### Pedidos (`entity_type = "pedido"`):
1. **pendiente → entregado**: Cuando el saldo se paga completamente
   - Se registra automáticamente cuando `saldo_pendiente <= 0`
   - Nota incluye el monto del último pago

2. **cualquier estado → vencido**: Automático después de 75 días
   - Se registra automáticamente por el sistema
   - (Pendiente de implementar el registro)

## API Endpoints

### GET `/status-history/{entity_type}/{entity_id}`
Obtiene el historial de cambios de estado para una venta o pedido.

**Parámetros:**
- `entity_type`: "sale" o "pedido"
- `entity_id`: ID de la entidad

**Respuesta:**
```json
[
  {
    "id": 1,
    "old_status": "pendiente",
    "new_status": "pagado",
    "user_email": "admin@example.com",
    "notes": "Abono de $500.00 - Venta completamente pagada",
    "created_at": "2025-11-08T12:30:00"
  }
]
```

### PATCH `/credits/sales/{sale_id}/entregado`
Marca una venta como entregada (solo para ventas pagadas).

## Interfaz de Usuario

### Gestión de Abonos
- **Botón "📋 Historial"**: Abre modal con historial de pagos y estados
- **Botón "✓ Marcar entregado"**: Aparece solo en ventas pagadas

### Gestión de Pedidos
- **Botón "Historial"**: Abre modal con historial de pagos y estados

### Modal de Historial
El modal muestra dos secciones:

1. **Información General**: Cliente, producto, total, abonos, saldo
2. **Tabla de Abonos**: Fecha, concepto, monto, método, notas
3. **Historial de Estados** (nuevo): Fecha, usuario, cambio de estado, notas

**Formato de cambio de estado:**
```
pendiente → pagado
```

## Migración

Ejecutar `migration_status_history.sql` en la base de datos de producción:

```bash
docker cp migration_status_history.sql erppos-db:/tmp/
docker exec erppos-db psql -U erpuser -d erppos -f /tmp/migration_status_history.sql
```

## Beneficios

1. **Trazabilidad completa**: Saber quién hizo cada cambio y cuándo
2. **Auditoría**: Cumplir con requisitos de auditoría
3. **Resolución de problemas**: Identificar cuándo y por qué cambió un estado
4. **Transparencia**: Los usuarios pueden ver el historial completo
5. **Seguridad**: Registro inmutable de cambios (no se pueden editar o eliminar)

## Próximas Mejoras

- [ ] Registrar cambio automático a "vencido" con el usuario del sistema
- [ ] Agregar filtro de historial por rango de fechas
- [ ] Exportar historial de estados a Excel
- [ ] Notificaciones cuando cambia un estado

