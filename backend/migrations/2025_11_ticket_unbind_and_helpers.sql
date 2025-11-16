-- Ticket Unbind and Helpers
-- Usage:
--  - Set the constants 'v_ticket_id', and optionally 'v_sale_id' or 'v_pedido_id'
--  - Run the whole script once in pgAdmin/psql
-- What it does:
--  - Safely unbinds a ticket from a sale/pedido without breaking unique constraints
--  - Optionally restores ticket to legacy kind to avoid clashes
--  - Provides preview queries

BEGIN;

DO $$
DECLARE
  -- CHANGE THESE VALUES BEFORE RUNNING
  v_ticket_id   INTEGER := 39;  -- Ticket to unbind
  v_sale_id     INTEGER := NULL;  -- If you want to only unbind when it belongs to this sale (optional)
  v_pedido_id   INTEGER := NULL;  -- If you want to only unbind when it belongs to this pedido (optional)

  -- Strategy for kind after unbind: 'sale-legacy' or 'orphaned'
  v_new_kind    TEXT := 'orphaned';

  v_tenant_id   INTEGER;
  v_old_sale_id INTEGER;
  v_old_pedido_id INTEGER;
  v_old_kind    TEXT;
BEGIN
  -- Preview current state
  RAISE NOTICE 'Current ticket state:';
  PERFORM 1;
  -- no-op

  -- Fetch and validate
  SELECT tenant_id, sale_id, pedido_id, kind
  INTO v_tenant_id, v_old_sale_id, v_old_pedido_id, v_old_kind
  FROM tickets
  WHERE id = v_ticket_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Ticket id % not found', v_ticket_id;
  END IF;

  IF v_sale_id IS NOT NULL AND v_old_sale_id IS DISTINCT FROM v_sale_id THEN
    RAISE EXCEPTION 'Ticket % does not belong to sale_id % (has %)', v_ticket_id, v_sale_id, v_old_sale_id;
  END IF;
  IF v_pedido_id IS NOT NULL AND v_old_pedido_id IS DISTINCT FROM v_pedido_id THEN
    RAISE EXCEPTION 'Ticket % does not belong to pedido_id % (has %)', v_ticket_id, v_pedido_id, v_old_pedido_id;
  END IF;

  -- Unbind: set sale_id/pedido_id NULL and set kind to legacy/orphaned
  UPDATE tickets
  SET sale_id = NULL,
      pedido_id = NULL,
      kind = v_new_kind
  WHERE id = v_ticket_id;
END$$;

-- Preview helpers
-- List tickets by sale
-- SELECT id, tenant_id, sale_id, pedido_id, kind, created_at FROM tickets WHERE sale_id = 1 ORDER BY created_at;
-- List tickets by pedido
-- SELECT id, tenant_id, sale_id, pedido_id, kind, created_at FROM tickets WHERE pedido_id = 10 ORDER BY created_at;

COMMIT;


