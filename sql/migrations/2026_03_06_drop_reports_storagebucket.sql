-- Remove StorageBucket from Reports to align with app/models.py
-- Run against PostgreSQL.

BEGIN;

ALTER TABLE "Reports"
    DROP COLUMN IF EXISTS "StorageBucket";

COMMIT;

