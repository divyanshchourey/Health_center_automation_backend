-- Align PostgreSQL schema with the current app/models.py
-- This removes columns and tables introduced by older migrations
-- that are no longer represented in the ORM models.
-- Run against PostgreSQL.

BEGIN;

-- InvestigationBookings: current model does not include PatientID
-- or the extra workflow metadata columns.
ALTER TABLE "InvestigationBookings"
    DROP COLUMN IF EXISTS "PatientID",
    DROP COLUMN IF EXISTS "RequestedAt",
    DROP COLUMN IF EXISTS "ApprovedAt",
    DROP COLUMN IF EXISTS "RejectedAt",
    DROP COLUMN IF EXISTS "BillAmount",
    DROP COLUMN IF EXISTS "BillGeneratedAt",
    DROP COLUMN IF EXISTS "BillStatus";

-- The current model does not define lab-owner mapping or lab-test mapping.
ALTER TABLE "LabCenters"
    DROP COLUMN IF EXISTS "OwnerUserID";

DROP TABLE IF EXISTS "LabInvestigations";

-- Reports: keep only ReportID, BookingID, FilePath from the current model.
ALTER TABLE "Reports"
    DROP COLUMN IF EXISTS "PatientID",
    DROP COLUMN IF EXISTS "Category",
    DROP COLUMN IF EXISTS "BillType",
    DROP COLUMN IF EXISTS "FileName",
    DROP COLUMN IF EXISTS "StorageBucket",
    DROP COLUMN IF EXISTS "UploadedAt";

-- LabCenterBilling: current model keeps only LabBillID, AppointmentID,
-- PaymentID, Amount, Date.
ALTER TABLE "LabCenterBilling"
    DROP COLUMN IF EXISTS "BookingID",
    DROP COLUMN IF EXISTS "PatientID",
    DROP COLUMN IF EXISTS "LabID",
    DROP COLUMN IF EXISTS "Status";

-- DoctorBilling: current model keeps only DBillID, AppointmentID,
-- PaymentID, Amount, Date.
ALTER TABLE "DoctorBilling"
    DROP COLUMN IF EXISTS "PatientID",
    DROP COLUMN IF EXISTS "DoctorID",
    DROP COLUMN IF EXISTS "Status";

COMMIT;
