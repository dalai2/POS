-- Crear tabla folio_counters si no existe
-- Esta tabla almacena los contadores de folios por tenant y tipo

BEGIN;

-- Crear tabla folio_counters
CREATE TABLE IF NOT EXISTS folio_counters (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL,
    next_seq INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_folio_counters_tenant_tipo UNIQUE (tenant_id, tipo)
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_folio_counters_tenant_id ON folio_counters(tenant_id);
CREATE INDEX IF NOT EXISTS idx_folio_counters_tipo ON folio_counters(tipo);

COMMIT;

