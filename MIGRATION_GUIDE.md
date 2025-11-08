# 📋 Guía de Migración a Producción

## Cambios Realizados en Esta Sesión (2025-11-07)

### ✅ Cambios en Base de Datos

**Tabla `productos_pedido`:**
1. ✅ Columnas renombradas:
   - `name` → `modelo` (modelo del producto - campo principal)
   - `tipo_joya` → `nombre` (tipo/nombre de joya)
   - `price` → `precio` (precio de venta)
   - **Eliminada columna `modelo` duplicada antigua si existía**
2. ✅ Agregada columna `peso` (VARCHAR(100)) - peso descriptivo
3. ✅ Agregada columna `category` (VARCHAR(100))
4. ✅ Columna `modelo` ahora es NOT NULL
5. ✅ Columna `precio` ahora es NOT NULL con default 0
6. ✅ Columna `cost_price` ahora es NOT NULL con default 0
7. ✅ Columna `disponible` ahora tiene default true

**IMPORTANTE:** La estructura final es:
- `modelo` (NOT NULL) - Modelo/descripción principal del producto
- `nombre` (nullable) - Tipo de joya (anillo, collar, etc)
- `precio` (NOT NULL) - Precio de venta
- `peso` (nullable) - Peso descriptivo
- Más campos de joyería: codigo, marca, color, quilataje, base, talla, peso_gramos, etc.

**Tabla `tasas_metal_pedido`:**
1. ✅ Agregada columna `tipo` (VARCHAR(20), default 'precio')
2. ✅ Índice creado en columna `tipo`
3. ✅ Permite separar tasas de costo y precio

**No se crearon nuevas tablas** - Solo modificaciones a columnas existentes.

---

## 🚀 Cómo Aplicar en Producción

### Opción 1: Usando Docker (Recomendado)

```bash
# 1. Hacer backup primero (IMPORTANTE)
docker exec erppos-db pg_dump -U erpuser erppos > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Aplicar la migración
docker exec -i erppos-db psql -U erpuser -d erppos < migration_2025_11_07.sql

# 3. Verificar que se aplicó correctamente
docker exec erppos-db psql -U erpuser -d erppos -c "\d productos_pedido"
```

### Opción 2: PostgreSQL Directo

```bash
# 1. Hacer backup
pg_dump -U erpuser -d erppos > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Aplicar migración
psql -U erpuser -d erppos -f migration_2025_11_07.sql
```

### Opción 3: Copiar y Pegar en pgAdmin

1. Abre `migration_2025_11_07.sql`
2. Copia todo el contenido
3. Pega en pgAdmin Query Tool
4. Ejecuta (F5)

---

## ⚠️ IMPORTANTE - Antes de Aplicar

### 1. **Haz un Backup Completo**

```bash
# Docker
docker exec erppos-db pg_dump -U erpuser erppos > backup_completo.sql

# PostgreSQL directo
pg_dump -U erpuser -d erppos > backup_completo.sql
```

### 2. **Verifica Datos Existentes**

Asegúrate de que tus datos no tengan valores NULL en campos críticos:

```sql
-- Revisar productos sin nombre
SELECT COUNT(*) FROM productos_pedido WHERE name IS NULL;

-- Revisar productos sin precio
SELECT COUNT(*) FROM productos_pedido WHERE price IS NULL;
```

### 3. **El Script Es Seguro**

- ✅ Usa transacciones (BEGIN...COMMIT)
- ✅ Actualiza valores NULL antes de agregar restricciones
- ✅ Es idempotente (se puede ejecutar múltiples veces)
- ✅ No elimina datos

---

## 🔍 Verificación Post-Migración

Después de aplicar la migración, verifica:

```sql
-- 1. Verificar estructura de productos_pedido
\d productos_pedido

-- 2. Verificar que category existe
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'productos_pedido' AND column_name = 'category';

-- 3. Contar productos
SELECT COUNT(*) as total_productos FROM productos_pedido;
```

---

## 🔄 Rollback (Si Algo Sale Mal)

Si necesitas revertir los cambios:

```bash
# 1. Restaurar desde backup
docker exec -i erppos-db psql -U erpuser -d erppos < backup_completo.sql

# O con PostgreSQL directo
psql -U erpuser -d erppos < backup_completo.sql
```

---

## 📝 Cambios en Código Backend/Frontend

### Backend (`backend/app/routes/`)
- ✅ `reports.py` - Agregado endpoint de pedidos en corte de caja detallado
- ✅ `productos_pedido.py` - Lógica de estado "vencido" (75 días)
- ✅ `credits.py` - Lógica de estado "vencido" para abonos
- ✅ `admin.py` - CRUD completo de usuarios (PUT, DELETE)

### Frontend (`frontend/src/pages/`)
- ✅ `ProductsPage.tsx` - Filtros por quilataje, modelo, talla
- ✅ `PedidosPage.tsx` - Filtros similares + carrito optimizado
- ✅ `GestionPedidosPage.tsx` - Columna vendedor + notas cliente
- ✅ `ReportsPage.tsx` - Pedidos en corte de caja + sin selector de tipo
- ✅ `UsersPage.tsx` - CRUD completo (solo owner)

**Estos cambios de código ya están en tu repositorio local** y solo necesitas:
1. Hacer commit
2. Push a tu repositorio
3. Pull en producción
4. Reiniciar contenedores Docker

---

## 🐳 Reiniciar Servicios en Producción

Después de aplicar la migración SQL:

```bash
# 1. Reiniciar backend para aplicar cambios de código
docker restart erppos-backend

# 2. Verificar logs
docker logs erppos-backend --tail 20

# 3. Reiniciar frontend si es necesario
docker restart erppos-frontend
```

---

## ✅ Checklist de Migración

- [ ] Backup de base de datos completo
- [ ] Aplicar migration_2025_11_07.sql
- [ ] Verificar estructura con `\d productos_pedido`
- [ ] Hacer commit de cambios de código
- [ ] Push a repositorio
- [ ] Pull en servidor de producción
- [ ] Reiniciar contenedores Docker
- [ ] Verificar que la aplicación funciona correctamente
- [ ] Probar funcionalidades nuevas (filtros, pedidos, usuarios)

---

## 🆘 Soporte

Si algo sale mal:
1. Restaura desde el backup
2. Revisa los logs: `docker logs erppos-backend`
3. Verifica que los contenedores estén corriendo: `docker ps`

---

**Fecha de creación:** 2025-11-07  
**Versión:** 1.0  
**Autor:** Sistema ERP-POS


