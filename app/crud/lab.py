from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]
from sqlalchemy import Date, cast, func

from app import models, schemas
from app.crud import patient as crud_patient

BOOKING_PENDING = "PENDING"
BOOKING_APPROVED = "APPROVED"
BOOKING_REJECTED = "REJECTED"
BOOKING_BILL_GENERATED = "BILL_GENERATED"
BOOKING_COMPLETED = "COMPLETED"

def list_labs(db: Session):
    return (
        db.query(
            models.LabCenter.LabID,
            models.LabCenter.Name,
            models.LabCenter.Address,
            models.LabCenter.Contact,
            models.LabCenter.AccreditationNumber,
            models.LabCenter.ApprovedByAdmin,
            models.LabCenter.CreatedAt,
        )
        .filter(models.LabCenter.ApprovedByAdmin == True)  # noqa: E712
        .all()
    )

    
def list_tests_by_lab(db: Session, lab_id: int):
    lab_exists = (
        db.query(models.LabCenter.LabID)
        .filter(
            models.LabCenter.LabID == lab_id,
            models.LabCenter.ApprovedByAdmin == True,  # noqa: E712
        )
        .first()
    )
    if not lab_exists:
        raise ValueError("Lab not found or not approved.")

    return (
        db.query(
            models.Investigation.InvestigationID,
            models.Investigation.Name,
            models.Investigation.Description,
            models.Investigation.DefaultRate,
        )
        .order_by(models.Investigation.Name.asc())
        .all()
    )


def list_own_lab_tests(db: Session, lab_id: int):
    lab_exists = (
        db.query(models.LabCenter.LabID)
        .filter(
            models.LabCenter.LabID == lab_id,
            models.LabCenter.ApprovedByAdmin == True,  # noqa: E712
        )
        .first()
    )
    if not lab_exists:
        raise ValueError("Lab not found or not approved.")

    return (
        db.query(
            models.Investigation.InvestigationID,
            models.Investigation.Name,
            models.Investigation.Description,
            models.Investigation.DefaultRate,
        )
        .join(
            models.InvestigationBooking,
            models.Investigation.InvestigationID == models.InvestigationBooking.InvestigationID,
        )
        .filter(models.InvestigationBooking.LabID == lab_id)
        .distinct()
        .order_by(models.Investigation.Name.asc())
        .all()
    )


def create_investigation(
    db: Session,
    payload: schemas.InvestigationCreate,
):
    normalized_name = (payload.Name or "").strip()
    if not normalized_name:
        raise ValueError("Investigation name is required.")

    if payload.DefaultRate is not None and payload.DefaultRate <= 0:
        raise ValueError("DefaultRate must be greater than 0.")

    existing = (
        db.query(models.Investigation)
        .filter(func.lower(models.Investigation.Name) == normalized_name.lower())
        .first()
    )
    if existing:
        raise ValueError("Investigation already exists.")

    investigation = models.Investigation(
        Name=normalized_name,
        Description=payload.Description,
        DefaultRate=Decimal(str(payload.DefaultRate)) if payload.DefaultRate is not None else None,
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    return {
        "InvestigationID": investigation.InvestigationID,
        "Name": investigation.Name,
        "Description": investigation.Description,
        "DefaultRate": float(investigation.DefaultRate) if investigation.DefaultRate is not None else None,
    }


def create_booking(
    db: Session,
    patient_id: int,
    payload: schemas.InvestigationBookingCreate,
):
    patient = (
        db.query(models.User)
        .filter(models.User.UserID == patient_id, models.User.RoleID == 3)
        .first()
    )
    if not patient:
        raise ValueError("Patient not found.")

    lab = (
        db.query(models.LabCenter.LabID)
        .filter(
            models.LabCenter.LabID == payload.LabID,
            models.LabCenter.ApprovedByAdmin == True,  # noqa: E712
        )
        .first()
    )
    if not lab:
        raise ValueError("Lab not found or not approved.")

    investigation = (
        db.query(models.Investigation)
        .filter(models.Investigation.InvestigationID == payload.InvestigationID)
        .first()
    )
    if not investigation:
        raise ValueError("Investigation not found.")

    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.AppointmentID == payload.AppointmentID)
        .first()
    )
    if not appointment:
        raise ValueError("Appointment not found.")
    if appointment.PatientID != patient_id:
        raise ValueError("Appointment does not belong to this patient.")
    if appointment.LabID is not None and appointment.LabID != payload.LabID:
        raise ValueError("Appointment LabID does not match booking LabID.")
    appointment.LabID = payload.LabID

    existing_booking = (
        db.query(models.InvestigationBooking)
        .filter(
            models.InvestigationBooking.AppointmentID == payload.AppointmentID,
            models.InvestigationBooking.InvestigationID == payload.InvestigationID,
            models.InvestigationBooking.LabID == payload.LabID,
        )
        .first()
    )
    if existing_booking:
        raise ValueError("Booking already exists for this appointment and investigation.")

    booking = models.InvestigationBooking(
        AppointmentID=payload.AppointmentID,
        InvestigationID=payload.InvestigationID,
        LabID=payload.LabID,
        InvestigationDate=datetime.utcnow().date(),
        Status=BOOKING_PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def list_lab_bookings(
    db: Session,
    lab_id: int,
    status: str | None = None,
    query_date: date | None = None,
):
    query = (
        db.query(models.InvestigationBooking)
        .join(models.Appointment, models.InvestigationBooking.AppointmentID == models.Appointment.AppointmentID)
        .filter(models.InvestigationBooking.LabID == lab_id)
    )
    if status:
        normalized_status = status.strip().upper()
        query = query.filter(
            func.upper(func.trim(models.InvestigationBooking.Status)) == normalized_status
        )
    if query_date is not None:
        query = query.filter(cast(models.Appointment.DateTime, Date) == query_date)
    return query.order_by(models.InvestigationBooking.BookingID.desc()).all()



def list_patient_bookings(
    db: Session,
    patient_id: int,
    query_date: date | None = None,
):
    query = (
        db.query(models.InvestigationBooking)
        .join(models.Appointment, models.InvestigationBooking.AppointmentID == models.Appointment.AppointmentID)
        .filter(models.Appointment.PatientID == patient_id)
    )

    if query_date is not None:
        query = query.filter(cast(models.Appointment.DateTime, Date) == query_date)

    return query.order_by(models.InvestigationBooking.BookingID.desc()).all()


def approve_booking(
    db: Session,
    lab_id: int,
    booking_id: int,
    action: str,
):
    normalized = action.strip().lower()
    if normalized not in {"approve", "reject"}:
        raise ValueError("Invalid action. Use approve or reject.")

    booking = (
        db.query(models.InvestigationBooking)
        .filter(
            models.InvestigationBooking.BookingID == booking_id,
            models.InvestigationBooking.LabID == lab_id,
        )
        .first()
    )
    if not booking:
        raise ValueError("Booking not found.")

    if booking.Status in {
        BOOKING_APPROVED,
        BOOKING_REJECTED,
        BOOKING_BILL_GENERATED,
        BOOKING_COMPLETED,
    }:
        raise ValueError("Booking status transition is not allowed.")

    if normalized == "approve":
        booking.Status = BOOKING_APPROVED
    else:
        booking.Status = BOOKING_REJECTED

    db.commit()
    db.refresh(booking)
    return booking


def generate_bill(
    db: Session,
    lab_id: int,
    booking_id: int,
    amount: float,
):
    booking = (
        db.query(models.InvestigationBooking)
        .filter(
            models.InvestigationBooking.BookingID == booking_id,
            models.InvestigationBooking.LabID == lab_id,
        )
        .first()
    )
    if not booking:
        raise ValueError("Booking not found.")

    if booking.Status != BOOKING_APPROVED:
        raise ValueError("Bill can be generated only for APPROVED booking.")

    if amount <= 0:
        raise ValueError("Bill amount must be greater than 0.")

    existing_bill = (
        db.query(models.LabCenterBilling)
        .filter(models.LabCenterBilling.AppointmentID == booking.AppointmentID)
        .first()
    )
    if existing_bill:
        raise ValueError("Bill is already generated for this appointment.")

    booking.Status = BOOKING_BILL_GENERATED
    generated_at = datetime.utcnow()
    bill = models.LabCenterBilling(
        AppointmentID=booking.AppointmentID,
        Amount=Decimal(str(amount)),
        Date=generated_at,
    )
    db.add(bill)

    db.commit()
    db.refresh(bill)
    return bill


def upload_booking_report(
    db: Session,
    lab_id: int,
    booking_id: int,
    file_name: str,
    pdf_bytes: bytes,
    content_type: str | None = None,
):
    booking = (
        db.query(models.InvestigationBooking)
        .filter(
            models.InvestigationBooking.BookingID == booking_id,
            models.InvestigationBooking.LabID == lab_id,
        )
        .first()
    )
    if not booking:
        raise ValueError("Booking not found for this lab.")

    return crud_patient.upload_patient_pdf(
        db=db,
        booking_id=booking_id,
        file_name=file_name,
        pdf_bytes=pdf_bytes,
        content_type=content_type,
    )


def get_patient_bill(db: Session, patient_id: int, booking_id: int):
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
        raise ValueError("Booking not found.")

    bill = (
        db.query(models.LabCenterBilling)
        .filter(models.LabCenterBilling.AppointmentID == booking.AppointmentID)
        .first()
    )
    if not bill:
        raise ValueError("Booking not found.")
    return bill


def get_lab_bill_by_booking(
    db: Session,
    lab_id: int,
    booking_id: int,
):
    booking = (
        db.query(models.InvestigationBooking)
        .filter(
            models.InvestigationBooking.BookingID == booking_id,
            models.InvestigationBooking.LabID == lab_id,
        )
        .first()
    )
    if not booking:
        raise ValueError("Booking not found for this lab.")

    bill = (
        db.query(models.LabCenterBilling)
        .filter(models.LabCenterBilling.AppointmentID == booking.AppointmentID)
        .first()
    )
    if not bill:
        raise ValueError("Lab bill not found.")

    return bill


def record_lab_bill_payment(
    db: Session,
    lab_id: int,
    booking_id: int,
    payload: schemas.PaymentCreate,
):
    booking = (
        db.query(models.InvestigationBooking)
        .filter(
            models.InvestigationBooking.BookingID == booking_id,
            models.InvestigationBooking.LabID == lab_id,
        )
        .first()
    )
    if not booking:
        raise ValueError("Booking not found for this lab.")

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
        Status=(payload.Status or "SUCCESS").strip(),
        Date=datetime.utcnow(),
    )
    db.add(payment)
    db.flush()

    bill.PaymentID = payment.PaymentID
    booking.Status = BOOKING_COMPLETED

    db.commit()
    db.refresh(payment)
    db.refresh(bill)
    return payment
