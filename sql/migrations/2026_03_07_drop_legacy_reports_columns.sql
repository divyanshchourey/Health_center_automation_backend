-- Drop legacy/unnecessary columns from Reports table.
-- Safe to run multiple times.

BEGIN;

ALTER TABLE "Reports"
    DROP COLUMN IF EXISTS "FileType",
    DROP COLUMN IF EXISTS "InvestigationBooking";

COMMIT;
