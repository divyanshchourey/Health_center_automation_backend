-- Phase 1 migration: lab-test catalog + booking lifecycle fields
-- Run against PostgreSQL.

BEGIN;

CREATE TABLE IF NOT EXISTS "LabInvestigations" (
    "LabInvestigationID" SERIAL PRIMARY KEY,
    "LabID" INTEGER NOT NULL REFERENCES "LabCenters"("LabID"),
    "InvestigationID" INTEGER NOT NULL REFERENCES "Investigations"("InvestigationID"),
    "Price" DECIMAL NOT NULL,
    "IsActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "TurnaroundHours" INTEGER
);

CREATE INDEX IF NOT EXISTS "ix_LabInvestigations_LabID"
    ON "LabInvestigations" ("LabID");

CREATE INDEX IF NOT EXISTS "ix_LabInvestigations_InvestigationID"
    ON "LabInvestigations" ("InvestigationID");

ALTER TABLE "InvestigationBookings"
    ALTER COLUMN "AppointmentID" DROP NOT NULL;

ALTER TABLE "InvestigationBookings"
    ADD COLUMN IF NOT EXISTS "PatientID" INTEGER REFERENCES "Users"("UserID"),
    ADD COLUMN IF NOT EXISTS "RequestedAt" TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS "ApprovedAt" TIMESTAMP WITHOUT TIME ZONE,
    ADD COLUMN IF NOT EXISTS "RejectedAt" TIMESTAMP WITHOUT TIME ZONE,
    ADD COLUMN IF NOT EXISTS "BillAmount" DECIMAL,
    ADD COLUMN IF NOT EXISTS "BillGeneratedAt" TIMESTAMP WITHOUT TIME ZONE,
    ADD COLUMN IF NOT EXISTS "BillStatus" VARCHAR;

CREATE INDEX IF NOT EXISTS "ix_InvestigationBookings_PatientID"
    ON "InvestigationBookings" ("PatientID");

COMMIT;
