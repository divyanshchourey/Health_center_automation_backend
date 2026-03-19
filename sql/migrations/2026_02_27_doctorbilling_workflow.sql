-- Doctor billing workflow migration
-- Uses existing DoctorBilling table (no new table).

BEGIN;

ALTER TABLE "DoctorBilling"
    ALTER COLUMN "PaymentID" DROP NOT NULL;

ALTER TABLE "DoctorBilling"
    ADD COLUMN IF NOT EXISTS "PatientID" INTEGER REFERENCES "Users"("UserID"),
    ADD COLUMN IF NOT EXISTS "DoctorID" INTEGER REFERENCES "Users"("UserID"),
    ADD COLUMN IF NOT EXISTS "Status" VARCHAR NOT NULL DEFAULT 'GENERATED';

CREATE INDEX IF NOT EXISTS "ix_DoctorBilling_AppointmentID"
    ON "DoctorBilling" ("AppointmentID");

CREATE INDEX IF NOT EXISTS "ix_DoctorBilling_PatientID"
    ON "DoctorBilling" ("PatientID");

CREATE INDEX IF NOT EXISTS "ix_DoctorBilling_DoctorID"
    ON "DoctorBilling" ("DoctorID");

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_DoctorBilling_AppointmentID'
    ) THEN
        ALTER TABLE "DoctorBilling"
            ADD CONSTRAINT "uq_DoctorBilling_AppointmentID" UNIQUE ("AppointmentID");
    END IF;
END $$;

COMMIT;
