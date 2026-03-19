from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session
from app import models, schemas
from app.crud import profile_image as crud_profile_image

DOCTOR_CHECKUP_PRICING: dict[str, Decimal] = {
    "general_checkup": Decimal("500.00"),
    "consultation": Decimal("800.00"),
    "follow_up": Decimal("400.00"),
    "emergency": Decimal("1200.00"),
}


def _normalize_checkup_category(category: str) -> str:
    normalized = (category or "").strip().lower().replace(" ", "_")
    if normalized not in DOCTOR_CHECKUP_PRICING:
        allowed = ", ".join(sorted(DOCTOR_CHECKUP_PRICING.keys()))
        raise ValueError(f"Invalid checkup category. Use one of: {allowed}.")
    return normalized


def get_doctor_checkup_price_list():
    return [
        {"Type": checkup_type, "Amount": float(amount)}
        for checkup_type, amount in sorted(DOCTOR_CHECKUP_PRICING.items())
    ]


def get_all_employees(db: Session):
    """Fetch all employees with basic user details"""
    return db.query(
        models.User.UserID,
        models.User.FirstName,
        models.User.LastName,
        models.User.Phone,
        models.Employee.EProfilePhoto,
        models.Employee.Division,
        models.Employee.Ward,
        models.Employee.Designation,
        models.Employee.Status
    ).join(models.Employee, models.User.UserID == models.Employee.EmployeeID).all()


def get_employee_profile(db: Session, user_id: int):
    """Fetch employee profile"""
    return db.query(models.Employee).filter(models.Employee.EmployeeID == user_id).first()


def create_or_update_employee_profile(db: Session, user_id: int, data: schemas.EmployeeCreate):
    """Create or update employee profile"""
    profile = db.query(models.Employee).filter(models.Employee.EmployeeID == user_id).first()
    data_dict = data.model_dump(exclude_unset=True)

    if profile:
        for key, value in data_dict.items():
            setattr(profile, key, value)
    else:
        profile = models.Employee(EmployeeID=user_id, **data_dict)
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


def delete_employee_profile(db: Session, user_id: int):
    """Delete employee profile"""
    profile = db.query(models.Employee).filter(models.Employee.EmployeeID == user_id).first()
    if profile:
        db.delete(profile)
        db.commit()
        return True
    return False

def get_todays_appointments(db: Session):
    today = date.today()
    rows = (
        db.query(
            models.Appointment.AppointmentID,
            models.Appointment.PatientID,
            models.Appointment.DoctorID,
            models.Appointment.DateTime,
            models.Appointment.Type,
            models.Appointment.Status,
        )
        .filter(cast(models.Appointment.DateTime, Date) == today)
        .all()
    )
    return [
        {
            "AppointmentID": row.AppointmentID,
            "PatientID": row.PatientID,
            "DoctorID": row.DoctorID,
            "DateTime": row.DateTime,
            "Type": row.Type,
            "Status": row.Status,
        }
        for row in rows
    ]


def get_all_appointments_by_date(db: Session, query_date: date):
    """Fetch all appointments on a specific date"""
    appointments = (
        db.query(
            models.Appointment.AppointmentID,
            models.Appointment.PatientID,
            models.Appointment.DoctorID,
            models.Appointment.DateTime,
            models.Appointment.Type,
            models.Appointment.Status,
            models.User.FirstName.label("PatientFirstName"),
            models.User.LastName.label("PatientLastName"),
        )
        .join(models.PatientProfile, models.Appointment.PatientID == models.PatientProfile.PatientID)
        .join(models.User, models.PatientProfile.PatientID == models.User.UserID)
        .filter(cast(models.Appointment.DateTime, Date) == query_date)
        .all()
    )

    results = []
    for appt in appointments:
        patient_name = f"{appt.PatientFirstName or ''} {appt.PatientLastName or ''}".strip() or "Unknown"
        doctor_name = "Unknown"
        doctor_user = db.query(models.User).filter(models.User.UserID == appt.DoctorID).first()
        if doctor_user:
            doctor_name = f"{doctor_user.FirstName} {doctor_user.LastName}".strip()

        results.append(schemas.AppointmentEmployeeResponse(
            AppointmentID=appt.AppointmentID,
            PatientID=appt.PatientID,
            PatientName=patient_name,
            DoctorID=appt.DoctorID,
            DoctorName=doctor_name,
            DateTime=appt.DateTime,
            Type=appt.Type,
            Status=appt.Status
        ))
    
    return results


def delete_appointment(db: Session, appointment_id: int):
    """Delete an appointment by ID"""
    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.AppointmentID == appointment_id)
        .first()
    )
    if not appointment:
        return False

    consultation = (
        db.query(models.Consultation)
        .filter(models.Consultation.AppointmentID == appointment_id)
        .first()
    )
    if consultation:
        db.delete(consultation)

    doctor_bill = (
        db.query(models.DoctorBilling)
        .filter(models.DoctorBilling.AppointmentID == appointment_id)
        .first()
    )
    if doctor_bill:
        db.delete(doctor_bill)

    lab_bills = (
        db.query(models.LabCenterBilling)
        .filter(models.LabCenterBilling.AppointmentID == appointment_id)
        .all()
    )
    for lab_bill in lab_bills:
        db.delete(lab_bill)

    (
        db.query(models.InvestigationBooking)
        .filter(models.InvestigationBooking.AppointmentID == appointment_id)
        .update({"AppointmentID": None}, synchronize_session=False)
    )

    db.delete(appointment)
    db.commit()
    return True


def generate_doctor_bill(
    db: Session,
    appointment_id: int,
):
    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.AppointmentID == appointment_id)
        .first()
    )
    if not appointment:
        raise ValueError("Appointment not found.")

    existing = (
        db.query(models.DoctorBilling)
        .filter(models.DoctorBilling.AppointmentID == appointment_id)
        .first()
    )
    if existing:
        raise ValueError("Doctor bill already generated for this appointment.")

    appointment_type = (appointment.Type or "").strip()
    if not appointment_type:
        raise ValueError("Appointment type is missing.")

    normalized_category = _normalize_checkup_category(appointment_type)
    amount = DOCTOR_CHECKUP_PRICING[normalized_category]

    appointment.Type = normalized_category

    bill = models.DoctorBilling(
        AppointmentID=appointment_id,
        PaymentID=None,
        Amount=amount,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill



def get_doctor_bill_by_appointment(db: Session, appointment_id: int):
    return (
        db.query(models.DoctorBilling)
        .filter(models.DoctorBilling.AppointmentID == appointment_id)
        .first()
    )


def record_doctor_bill_payment(
    db: Session,
    appointment_id: int,
    payload: schemas.PaymentCreate,
):
    bill = (
        db.query(models.DoctorBilling)
        .filter(models.DoctorBilling.AppointmentID == appointment_id)
        .first()
    )
    if not bill:
        raise ValueError("Doctor bill not found.")
    if bill.PaymentID is not None:
        raise ValueError("Doctor bill is already paid.")

    payment = models.Payment(
        Method=payload.Method.strip(),
        TransactionRef=(payload.TransactionRef or "").strip() or None,
        Status=(payload.Status or "SUCCESS").strip(),
        Date=datetime.utcnow(),
    )
    db.add(payment)
    db.flush()

    bill.PaymentID = payment.PaymentID

    db.commit()
    db.refresh(payment)
    db.refresh(bill)
    return payment


def upload_or_update_employee_profile_image(
    db: Session,
    employee_id: int,
    file_name: str,
    file_bytes: bytes,
    content_type: str | None,
):
    return crud_profile_image.upsert_profile_image(
        db=db,
        user_id=employee_id,
        role_type="employee",
        file_name=file_name,
        file_bytes=file_bytes,
        content_type=content_type,
    )


def get_employee_profile_image(db: Session, employee_id: int):
    return crud_profile_image.get_profile_image_record(
        db=db,
        user_id=employee_id,
        role_type="employee",
    )


def get_employee_profile_image_download_url(
    file_path: str,
    storage_bucket: str,
    expires_in_seconds: int = 600,
):
    return crud_profile_image.create_profile_image_download_url(
        storage_path=file_path,
        storage_bucket=storage_bucket,
        expires_in_seconds=expires_in_seconds,
    )
