-- Consolidated migration (all-in-one)
-- Combines:
-- 1) 2026_02_27_phase1_lab_workflow.sql
-- 2) 2026_02_27_phase5_phase6_lab_auth_billing.sql
-- 3) 2026_02_27_patientdocuments_to_reports.sql
-- 4) 2026_02_27_doctorbilling_workflow.sql
-- Run against PostgreSQL.

BEGIN;

-- =========================
-- Phase 1: lab workflow
-- =========================
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

-- =========================
-- Phase 5 + 6: lab auth + billing
-- =========================
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

-- =========================
-- Patient documents -> Reports
-- =========================
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

INSERT INTO "Reports" ("PatientID", "Category", "BillType", "FileName", "StorageBucket", "FilePath", "UploadedAt")
SELECT
    pd."PatientID",
    pd."Category",
    pd."BillType",
    pd."FileName",
    pd."StorageBucket",
    pd."FilePath",
    pd."UploadedAt"
FROM "PatientDocuments" pd
LEFT JOIN "Reports" r ON r."FilePath" = pd."FilePath"
WHERE r."ReportID" IS NULL;

DROP TABLE IF EXISTS "PatientDocuments";

-- =========================
-- Doctor billing workflow
-- =========================
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
