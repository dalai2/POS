-- ============================================================================
-- PRODUCTION: Reset sales ID sequence
-- ============================================================================
-- This script resets the sales table ID sequence to start from 1
-- 
-- ⚠️ WARNING: DESTRUCTIVE OPERATION
-- This will DELETE ALL sales and related data. Only use if you're sure!
-- 
-- IMPORTANT:
-- 1. BACKUP your database before running this
-- 2. This will delete: sales, sale_items, payments, tickets, and status history
-- 3. This is IRREVERSIBLE
-- 4. Make sure no one is using the system during this operation
-- ============================================================================

-- Uncomment the BEGIN/COMMIT lines to run as a transaction
-- BEGIN;

-- Step 1: Confirm you want to proceed
DO $$
BEGIN
    RAISE NOTICE '⚠️  WARNING: This will delete ALL sales data!';
    RAISE NOTICE 'If you want to proceed, execute the commands below manually.';
    RAISE NOTICE 'Remove the COMMENT markers (--) from the DELETE statements.';
END $$;

-- Step 2: Delete related data first (foreign keys)

-- Delete tickets associated with sales
-- DELETE FROM tickets WHERE sale_id IS NOT NULL;

-- Delete status history for sales
-- DELETE FROM status_history WHERE entity_type = 'sale';

-- Delete credit payments
-- DELETE FROM credit_payments;

-- Delete sale items
-- DELETE FROM sale_items;

-- Step 3: Delete all sales
-- DELETE FROM sales;

-- Step 4: Reset the sequence to start from 1
-- ALTER SEQUENCE sales_id_seq RESTART WITH 1;

-- Step 5: Verify the sequence was reset
SELECT 
    'Current sequence value' as info,
    nextval('sales_id_seq') as next_id;

-- If the above returns 1, rollback and re-run to avoid consuming ID 1
-- ROLLBACK;

-- Step 6: Reset the sequence again to actually start from 1 for the next insert
-- ALTER SEQUENCE sales_id_seq RESTART WITH 1;

-- Verify final state
SELECT 
    'Final sequence value' as info,
    currval('sales_id_seq') as current_id,
    (SELECT COUNT(*) FROM sales) as total_sales;

-- COMMIT;

-- ============================================================================
-- Alternative: Reset sequence WITHOUT deleting data
-- ============================================================================
-- If you just want to reset the sequence to continue from the current max ID:
/*
SELECT setval('sales_id_seq', COALESCE((SELECT MAX(id) FROM sales), 0) + 1, false);
*/

-- ============================================================================
-- To reset to a specific number (e.g., if you want next sale to be #50):
/*
ALTER SEQUENCE sales_id_seq RESTART WITH 50;
*/

