-- Migración: Agregar tipo_pedido a tabla pedidos
-- Fecha: 2025-11-08

BEGIN;

-- 1. Agregar columna tipo_pedido con valor por defecto 'apartado'
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS tipo_pedido VARCHAR(20) DEFAULT 'apartado';

-- 2. Actualizar registros existentes para que tengan tipo_pedido = 'apartado'
UPDATE pedidos SET tipo_pedido = 'apartado' WHERE tipo_pedido IS NULL;

-- 3. Crear índice para mejorar búsquedas por tipo
CREATE INDEX IF NOT EXISTS idx_pedidos_tipo_pedido ON pedidos(tipo_pedido);

COMMIT;

-- Verificación
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'pedidos' AND column_name = 'tipo_pedido')
    THEN '✅ Columna tipo_pedido agregada correctamente'
    ELSE '❌ Error: columna tipo_pedido no existe'
    END as status;


