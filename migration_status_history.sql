-- Migration para agregar tabla de historial de estados
-- Fecha: 2025-11-08

-- Crear tabla status_history
CREATE TABLE IF NOT EXISTS status_history (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(20) NOT NULL,
    entity_id INTEGER NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_email VARCHAR(255) NOT NULL,
    notes VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejor performance
CREATE INDEX IF NOT EXISTS idx_status_history_tenant ON status_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_status_history_entity ON status_history(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_status_history_created_at ON status_history(created_at);

-- Verificar que la tabla se creó correctamente
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'status_history'
ORDER BY ordinal_position;

