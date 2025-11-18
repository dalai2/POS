-- Migración: Agregar columna notas_cliente a tabla apartados
-- Fecha: 2025-12
-- Descripción: Agrega campo para notas del cliente en apartados (recordatorios sobre el cliente o producto)

BEGIN;

-- Agregar columna notas_cliente a tabla apartados
ALTER TABLE apartados 
ADD COLUMN IF NOT EXISTS notas_cliente TEXT;

-- Verificar que la columna se agregó correctamente
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'apartados' 
AND column_name = 'notas_cliente';

COMMIT;

-- Nota: Esta migración es idempotente (se puede ejecutar múltiples veces sin problemas)
-- La columna es nullable, por lo que no afecta registros existentes

