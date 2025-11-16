-- ============================================================================
-- Add username column to users, unique per tenant (nullable) with optional backfill
-- ============================================================================
BEGIN;

-- 1) Add column if not exists
ALTER TABLE users
ADD COLUMN IF NOT EXISTS username VARCHAR(150);

-- 2) Create unique constraint per tenant for non-null usernames
-- Drop existing if misnamed (safety)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_users_tenant_username'
  ) THEN
    ALTER TABLE users DROP CONSTRAINT uq_users_tenant_username;
  END IF;
END $$;

-- Implement uniqueness using a partial unique index (NULLs allowed)
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_tenant_username
ON users(tenant_id, username)
WHERE username IS NOT NULL;

-- 3) Create index for lookups
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);

-- 4) Optional backfill: default username from email local-part if NULL
UPDATE users
SET username = split_part(email, '@', 1)
WHERE username IS NULL;

COMMIT;


