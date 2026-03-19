# Healthcare Automation Backend

FastAPI backend for multi-role healthcare operations:
- Patient
- Doctor
- Employee (staff)
- Lab owner

This project supports doctor appointments, consultations, lab test booking, bill generation, payment recording, and document storage.

## Tech Stack
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT auth
- Supabase storage (for profile images and patient PDFs)

## Roles
- `RoleID=1`: Admin
- `RoleID=2`: Doctor
- `RoleID=3`: Patient
- `RoleID=4`: Employee
- `RoleID=5`: Lab owner

## Main Data Flow
1. User registers and logs in (`/auth/register`, `/auth/login`).
2. Patient books doctor appointment.
3. Employee chooses checkup category and generates doctor bill for that appointment.
4. Patient pays doctor bill (creates `Payments` row and links to `DoctorBilling`).
5. Doctor creates consultation for the appointment.
6. Patient views consultation.
7. Patient selects lab, sees tests, books lab test.
8. Lab owner approves booking and generates lab bill.
9. Patient pays lab bill (creates `Payments` row and links to `LabCenterBilling`).
10. Patient/Employee upload and download PDFs from `Reports` (bill/report/prescription categories).

## Workflow By Actor

## 1) Patient Workflow
1. Register/Login:
- `POST /auth/register`
- `POST /auth/login` or `POST /auth/login/patient`

2. Maintain profile:
- `POST /patient/{user_id}` (create/update profile)
- `GET /patient/{user_id}` (view profile)

3. Book doctor appointment:
- `POST /patient/appointment`

4. View and pay doctor bill:
- `GET /patient/appointments/{appointment_id}/doctor-bill`
- `POST /patient/appointments/{appointment_id}/doctor-bill/pay`

5. View consultation:
- `GET /patient/appointments/{appointment_id}/consultation`

6. Lab flow:
- `GET /patient/labs`
- `GET /patient/labs/{lab_id}/tests`
- `POST /patient/labs/{lab_id}/bookings`
- `GET /patient/bookings`
- `GET /patient/bookings/{booking_id}/bill`
- `POST /patient/bookings/{booking_id}/bill/pay`

7. Documents:
- `POST /patient/upload/{category}`
- `GET /patient/documents/me`
- `GET /patient/documents/{document_id}/download`

## 2) Doctor Workflow
1. Maintain profile and profile image:
- `POST /doctor/{user_id}`
- `GET /doctor/{user_id}`
- `POST /doctor/profile-image`
- `PUT /doctor/profile-image`
- `GET /doctor/profile-image`

2. View appointments:
- `GET /doctor/{user_id}/appointments?date=YYYY-MM-DD`

3. Consultation actions:
- `POST /doctor/appointments/{appointment_id}/consultation` (create/update)
- `GET /doctor/appointments/{appointment_id}/consultation` (view)

## 3) Employee Workflow
1. Maintain profile and profile image:
- `POST /employee/{user_id}`
- `GET /employee/{user_id}`
- `POST /employee/profile-image`
- `PUT /employee/profile-image`
- `GET /employee/profile-image`

2. Appointment operations:
- `GET /employee/appointments/today`
- `GET /employee/appointments?date=YYYY-MM-DD`
- `DELETE /employee/appointments/{appointment_id}`

3. Doctor billing:
- `GET /employee/doctor-bills/categories` (category-price master, example: `general_checkup`, `consultation`)
- `POST /employee/doctor-bills/{appointment_id}`
- `GET /employee/doctor-bills/{appointment_id}`

4. Patient document operations:
- `POST /employee/upload/{patient_id}/{category}`
- `GET /employee/documents/{patient_id}`
- `GET /employee/documents/{document_id}/download`

## 4) Lab Owner Workflow
Lab owner identity is resolved from `LabCenters.OwnerUserID`.

1. Manage incoming bookings:
- `POST /lab/` (admin only, creates lab and maps `OwnerUserID`)
- `POST /lab/tests` (lab owner only, adds test mapping for own lab)
- `GET /lab/bookings`
- `PATCH /lab/bookings/{booking_id}/approve` with action `approve` or `reject`

2. Generate lab bill:
- `POST /lab/bookings/{booking_id}/bill`

## Billing and Payment Design
- Bill details are stored in `DoctorBilling`.
- Bill details are stored in `LabCenterBilling`.
- Payment transaction details are stored in `Payments`.

When patient pays a bill:
1. A row is inserted in `Payments` (`Method`, `TransactionRef`, `Status`, `Date`).
2. Bill table row gets `PaymentID` and status update to `PAID`.
3. For lab booking, booking status also moves to `COMPLETED`.

## Database Tables (Core)
- `Users`, `Roles`
- `PatientProfiles`, `DoctorProfiles`, `Employees`
- `Appointments`, `Consultations`
- `LabCenters`, `Investigations`, `LabInvestigations`, `InvestigationBookings`
- `DoctorBilling`, `LabCenterBilling`, `Payments`
- `Reports`

## Migrations
Run this consolidated SQL migration on your PostgreSQL database before starting API:
- `sql/migrations/2026_03_04_all_in_one.sql`

## Run Locally
1. Create and activate virtual environment.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Configure `.env` (DB URL, JWT secret, Supabase settings).
4. Start server:
```bash
uvicorn app.main:app --reload
```

## Notes
- `Base.metadata.create_all(bind=engine)` exists in `app/main.py`. In production, prefer controlled SQL migrations first.
- Consultation currently stores `PrescriptionFile` and `FollowUpRequired` in DB.
