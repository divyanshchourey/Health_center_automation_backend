-- Fix missing columns on Reports table required by current API code.
-- Safe to run multiple times.

BEGIN;

ALTER TABLE "Reports"
    ALTER COLUMN "BookingID" DROP NOT NULL;

ALTER TABLE "Reports"
    ADD COLUMN IF NOT EXISTS "PatientID" INTEGER REFERENCES "Users"("UserID"),
    ADD COLUMN IF NOT EXISTS "Category" VARCHAR,
    ADD COLUMN IF NOT EXISTS "BillType" VARCHAR,
    ADD COLUMN IF NOT EXISTS "FileName" VARCHAR,
    ADD COLUMN IF NOT EXISTS "StorageBucket" VARCHAR,
    ADD COLUMN IF NOT EXISTS "UploadedAt" TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_Reports_FilePath'
    ) THEN
        ALTER TABLE "Reports"
            ADD CONSTRAINT "uq_Reports_FilePath" UNIQUE ("FilePath");
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS "ix_Reports_PatientID"
    ON "Reports" ("PatientID");

COMMIT;
