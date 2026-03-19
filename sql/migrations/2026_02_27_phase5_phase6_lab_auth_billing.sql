-- Phase 5 + 6 migration
-- Uses one-lab-one-owner via LabCenters.OwnerUserID
-- and extends existing LabCenterBilling (no separate LabBills table).

BEGIN;

ALTER TABLE "LabCenters"
    ADD COLUMN IF NOT EXISTS "OwnerUserID" INTEGER UNIQUE REFERENCES "Users"("UserID");

ALTER TABLE "LabCenterBilling"
    ALTER COLUMN "AppointmentID" DROP NOT NULL;

ALTER TABLE "LabCenterBilling"
    ALTER COLUMN "PaymentID" DROP NOT NULL;

ALTER TABLE "LabCenterBilling"
    ADD COLUMN IF NOT EXISTS "BookingID" INTEGER UNIQUE REFERENCES "InvestigationBookings"("BookingID"),
    ADD COLUMN IF NOT EXISTS "PatientID" INTEGER REFERENCES "Users"("UserID"),
    ADD COLUMN IF NOT EXISTS "LabID" INTEGER REFERENCES "LabCenters"("LabID"),
    ADD COLUMN IF NOT EXISTS "Status" VARCHAR NOT NULL DEFAULT 'GENERATED';

CREATE INDEX IF NOT EXISTS "ix_LabCenterBilling_BookingID"
    ON "LabCenterBilling" ("BookingID");

CREATE INDEX IF NOT EXISTS "ix_LabCenterBilling_PatientID"
    ON "LabCenterBilling" ("PatientID");

CREATE INDEX IF NOT EXISTS "ix_LabCenterBilling_LabID"
    ON "LabCenterBilling" ("LabID");

DROP TABLE IF EXISTS "LabBills";
DROP TABLE IF EXISTS "LabUserMappings";

COMMIT;
