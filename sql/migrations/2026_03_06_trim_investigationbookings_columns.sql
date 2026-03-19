-- Trim InvestigationBookings columns to match app/models.py
-- Keeps: BookingID, AppointmentID, PatientID, InvestigationID, LabID, Status, ResultDate
-- Drops: InvestigationDate, RequestedAt, ApprovedAt, RejectedAt, BillAmount, BillGeneratedAt, BillStatus
-- Run against PostgreSQL.

BEGIN;

ALTER TABLE "InvestigationBookings"
    DROP COLUMN IF EXISTS "InvestigationDate",
    DROP COLUMN IF EXISTS "RequestedAt",
    DROP COLUMN IF EXISTS "ApprovedAt",
    DROP COLUMN IF EXISTS "RejectedAt",
    DROP COLUMN IF EXISTS "BillAmount",
    DROP COLUMN IF EXISTS "BillGeneratedAt",
    DROP COLUMN IF EXISTS "BillStatus";

COMMIT;

