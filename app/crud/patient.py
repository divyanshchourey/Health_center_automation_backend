from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from sqlalchemy import Date, cast
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from app import models, schemas
from app.core.supabase_client import supabase

BUCKET_NAME = "Pdf_patient"


def _upload_pdf_to_storage(storage_path: str, pdf_bytes: bytes):
    if supabase is None:
        raise RuntimeError("Storage service is not configured.")

    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            storage_path,
            pdf_bytes,
            {"content-type": "application/pdf"},
        )
    except Exception as exc:
        raise RuntimeError(f"Storage upload failed: {str(exc)}") from exc


def get_all_patients(db: Session):
    """Fetch all patients with basic user details."""
    return (
        db.query(
            models.User.UserID,
            models.User.FirstName,
            models.User.LastName,
            models.User.Phone,
            models.PatientProfile.BloodGroup,
            models.PatientProfile.RiskCategory,
        )
        .join(models.PatientProfile, models.User.UserID == models.PatientProfile.PatientID)
        .all()
    )

def get_all_doctors(db: Session):
    """Fetch all doctors with basic user details."""
    return (
        db.query(
            models.DoctorProfile.DProfilePhoto,
            models.User.UserID,
            models.User.FirstName,
            models.User.LastName,
            models.User.Phone,
            models.DoctorProfile.Specialization,
            models.DoctorProfile.ExperienceYears,
        )
        .join(models.DoctorProfile, models.User.UserID == models.DoctorProfile.DoctorID)
        .all()
    )


def get_patient_profile(db: Session, user_id: int):
    """Fetch patient profile."""
    return (
        db.query(models.PatientProfile)
        .filter(models.PatientProfile.PatientID == user_id)
        .first()
    )


def create_or_update_patient_profile(
    db: Session, user_id: int, data: schemas.PatientProfileCreate
):
    """Create or update patient profile."""
    profile = (
        db.query(models.PatientProfile)
        .filter(models.PatientProfile.PatientID == user_id)
        .first()
    )

    # Remove PatientID from data if it exists (prevents duplicate key error)
    data_dict = data.model_dump(exclude_unset=True)
    data_dict.pop("PatientID", None)

    if profile:
        for key, value in data_dict.items():
            setattr(profile, key, value)
    else:
        profile = models.PatientProfile(PatientID=user_id, **data_dict)
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


def delete_patient_profile(db: Session, user_id: int):
    """Delete patient profile."""
    profile = (
        db.query(models.PatientProfile)
        .filter(models.PatientProfile.PatientID == user_id)
        .first()
    )
    if profile:
        db.delete(profile)
        db.commit()
        return True
    return False


def create_appointment_for_patient(
    db: Session,
    patient_id: int,
    data: schemas.AppointmentCreate,
):
    if data.PatientID != patient_id:
        raise ValueError("PatientID in body must match the logged-in patient.")

    patient = (
        db.query(models.User)
        .filter(models.User.UserID == patient_id, models.User.RoleID == 3)
        .first()
    )
    if not patient:
        raise ValueError("Patient does not exist")

    doctor = (
        db.query(models.User)
        .join(models.DoctorProfile, models.User.UserID == models.DoctorProfile.DoctorID)
        .filter(models.User.UserID == data.DoctorID, models.User.RoleID == 2)
        .first()
    )
    if not doctor:
        raise ValueError("Doctor does not exist")

    appointment = models.Appointment(
        PatientID=patient_id,
        DoctorID=data.DoctorID,
        DateTime=data.DateTime,
        Type=data.Type,
        Status=data.Status or "PENDING",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def get_patient_appointments(
    db: Session,
    patient_id: int,
    query_date: date | None = None,
):
    query = (
        db.query(models.Appointment)
        .filter(models.Appointment.PatientID == patient_id)
    )

    if query_date is not None:
        query = query.filter(cast(models.Appointment.DateTime, Date) == query_date)

    return query.order_by(models.Appointment.DateTime.desc()).all()


def upload_patient_pdf(
    db: Session,
    booking_id: int,
    file_name: str,
    pdf_bytes: bytes,
    content_type: str | None = None,
    category: str | None = None,
    bill_type: str | None = None,
):
    booking = (
        db.query(models.InvestigationBooking)
        .join(models.Appointment, models.InvestigationBooking.AppointmentID == models.Appointment.AppointmentID)
        .filter(models.InvestigationBooking.BookingID == booking_id)
        .first()
    )
    if not booking or not booking.appointment:
        raise ValueError("Booking not found.")

    patient_id = booking.appointment.PatientID
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = Path(file_name).name
    final_name = f"{timestamp}_{safe_name}"
    storage_path = f"{patient_id}/report/booking_{booking_id}/{final_name}"

    _upload_pdf_to_storage(storage_path=storage_path, pdf_bytes=pdf_bytes)

    document = models.Report(
        BookingID=booking_id,
        FilePath=storage_path,
        FileType=(content_type or "application/pdf"),
    )
    db.add(document)
    try:
        db.commit()
        db.refresh(document)
    except Exception as exc:
        db.rollback()
        raise RuntimeError(f"Failed to save report metadata: {str(exc)}") from exc

    return {
        "document_id": document.DocumentID,
        "booking_id": document.BookingID,
        "path": document.FilePath,
        "file_name": document.FileName,
    }


def upload_consultation_prescription(
    db: Session,
    appointment_id: int,
    file_name: str,
    pdf_bytes: bytes,
):
    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.AppointmentID == appointment_id)
        .first()
    )
    if not appointment:
        raise ValueError("Appointment not found.")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = Path(file_name).name
    final_name = f"{timestamp}_{safe_name}"
    storage_path = f"{appointment.PatientID}/prescription/appointment_{appointment_id}/{final_name}"

    _upload_pdf_to_storage(storage_path=storage_path, pdf_bytes=pdf_bytes)

    consultation = (
        db.query(models.Consultation)
        .filter(models.Consultation.AppointmentID == appointment_id)
        .first()
    )

    if consultation:
        consultation.PrescriptionFile = storage_path
        if consultation.FollowUpRequired is None:
            consultation.FollowUpRequired = False
    else:
        consultation = models.Consultation(
            AppointmentID=appointment_id,
            PrescriptionFile=storage_path,
            FollowUpRequired=False,
        )
        db.add(consultation)

    try:
        db.commit()
        db.refresh(consultation)
    except Exception as exc:
        db.rollback()
        raise RuntimeError(f"Failed to save prescription metadata: {str(exc)}") from exc

    return {
        "consultation_id": consultation.ConsultationID,
        "appointment_id": consultation.AppointmentID,
        "path": consultation.PrescriptionFile,
    }


def get_patient_documents(
    db: Session,
    patient_id: int,
    category: str | None = None,
    booking_id: int | None = None,
):
    if category is not None:
        raise ValueError("The final report schema does not support categories.")

    query = (
        db.query(models.Report)
        .join(models.InvestigationBooking, models.Report.BookingID == models.InvestigationBooking.BookingID)
        .join(models.Appointment, models.InvestigationBooking.AppointmentID == models.Appointment.AppointmentID)
        .filter(models.Appointment.PatientID == patient_id)
    )
    if booking_id is not None:
        query = query.filter(models.Report.BookingID == booking_id)
    return query.order_by(models.Report.ReportID.desc()).all()


def get_patient_document(db: Session, patient_id: int, document_id: int):
    return (
        db.query(models.Report)
        .join(models.InvestigationBooking, models.Report.BookingID == models.InvestigationBooking.BookingID)
        .join(models.Appointment, models.InvestigationBooking.AppointmentID == models.Appointment.AppointmentID)
        .filter(
            models.Report.ReportID == document_id,
            models.Appointment.PatientID == patient_id,
        )
        .first()
    )


def get_document_by_id(db: Session, document_id: int):
    return (
        db.query(models.Report)
        .filter(models.Report.ReportID == document_id)
        .first()
    )


def list_reports_by_booking(db: Session, booking_id: int):
    booking_exists = (
        db.query(models.InvestigationBooking.BookingID)
        .filter(models.InvestigationBooking.BookingID == booking_id)
        .first()
    )
    if not booking_exists:
        raise ValueError("Booking not found.")

    return (
        db.query(models.Report)
        .filter(models.Report.BookingID == booking_id)
        .order_by(models.Report.ReportID.desc())
        .all()
    )


def create_document_download_url(
    storage_path: str,
    expires_in_seconds: int = 600,
):
    if supabase is None:
        raise RuntimeError("Storage service is not configured.")

    try:
        signed = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            storage_path,
            expires_in_seconds,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to create download URL: {str(exc)}") from exc

    if isinstance(signed, dict):
        for key in ("signedURL", "signedUrl", "signed_url"):
            url = signed.get(key)
            if url:
                return url

    url = getattr(signed, "signedURL", None) or getattr(signed, "signed_url", None)
    if url:
        return url

    raise RuntimeError("Failed to create download URL: invalid response from storage.")


def get_patient_doctor_bill(db: Session, patient_id: int, appointment_id: int):
    bill = (
        db.query(models.DoctorBilling)
        .join(models.Appointment, models.DoctorBilling.AppointmentID == models.Appointment.AppointmentID)
        .filter(
            models.DoctorBilling.AppointmentID == appointment_id,
            models.Appointment.PatientID == patient_id,
        )
        .first()
    )

    if not bill:
        return None

    doctor = (
        db.query(models.User)
        .filter(models.User.UserID == bill.appointment.DoctorID)
        .first()
    )

    doctor_name = None
    if doctor:
        doctor_name = f"{doctor.FirstName} {doctor.LastName or ''}".strip()

    return {
        "BillID": bill.BillID,
        "AppointmentID": bill.AppointmentID,
        "PatientID": bill.appointment.PatientID if bill.appointment else None,
        "DoctorID": bill.appointment.DoctorID if bill.appointment else None,
        "DoctorName": doctor_name,
        "Type": bill.Type,
        "BillAmount": float(bill.BillAmount),
        "BillStatus": bill.BillStatus,
        "BillGeneratedAt": bill.BillGeneratedAt,
    }



def get_patient_consultation_by_appointment(
    db: Session,
    patient_id: int,
    appointment_id: int,
):
    appointment = (
        db.query(models.Appointment.AppointmentID)
        .filter(
            models.Appointment.AppointmentID == appointment_id,
            models.Appointment.PatientID == patient_id,
        )
        .first()
    )
    if not appointment:
        raise ValueError("Appointment not found for this patient.")

    return (
        db.query(models.Consultation)
        .filter(models.Consultation.AppointmentID == appointment_id)
        .first()
    )


def pay_lab_bill(
    db: Session,
    patient_id: int,
    booking_id: int,
    payload: schemas.LabCenterBillingCreate,
):
    booking = (
        db.query(models.InvestigationBooking)
        .join(models.Appointment, models.InvestigationBooking.AppointmentID == models.Appointment.AppointmentID)
        .filter(
            models.InvestigationBooking.BookingID == booking_id,
            models.Appointment.PatientID == patient_id,
        )
        .first()
    )
    if not booking:
        raise ValueError("Lab booking not found.")

    bill = (
        db.query(models.LabCenterBilling)
        .filter(models.LabCenterBilling.AppointmentID == booking.AppointmentID)
        .first()
    )
    if not bill:
        raise ValueError("Lab bill not found.")
    if bill.PaymentID is not None:
        raise ValueError("Lab bill is already paid.")

    payment = models.Payment(
        Method=payload.Method.strip(),
        TransactionRef=(payload.TransactionRef or "").strip() or None,
        Status="SUCCESS",
        Date=datetime.utcnow(),
    )
    db.add(payment)
    db.flush()

    bill.PaymentID = payment.PaymentID
    booking.Status = "COMPLETED"

    db.commit()
    db.refresh(payment)
    db.refresh(bill)

    return {
        "BillType": "lab_bill",
        "BillID": bill.LabBillID,
        "PaymentID": payment.PaymentID,
        "Amount": float(Decimal(str(bill.Amount))),
        "BillStatus": bill.BillStatus,
        "PaymentStatus": payment.Status or "SUCCESS",
        "PaidAt": payment.Date,
    }


def pay_doctor_bill(
    db: Session,
    patient_id: int,
    appointment_id: int,
    payload: schemas.DoctorBillingCreate,
):
    bill = (
        db.query(models.DoctorBilling)
        .join(models.Appointment, models.DoctorBilling.AppointmentID == models.Appointment.AppointmentID)
        .filter(
            models.DoctorBilling.AppointmentID == appointment_id,
            models.Appointment.PatientID == patient_id,
        )
        .first()
    )
    if not bill:
        raise ValueError("Doctor bill not found.")
    if bill.PaymentID is not None:
        raise ValueError("Doctor bill is already paid.")

    payment = models.Payment(
        Method=payload.Method.strip(),
        TransactionRef=(payload.TransactionRef or "").strip() or None,
        Status="SUCCESS",
        Date=datetime.utcnow(),
    )
    db.add(payment)
    db.flush()

    bill.PaymentID = payment.PaymentID

    db.commit()
    db.refresh(payment)
    db.refresh(bill)

    return {
        "BillType": "doctor_bill",
        "BillID": bill.DBillID,
        "PaymentID": payment.PaymentID,
        "Amount": float(Decimal(str(bill.Amount))),
        "BillStatus": bill.BillStatus,
        "PaymentStatus": payment.Status or "SUCCESS",
        "PaidAt": payment.Date,
    }
