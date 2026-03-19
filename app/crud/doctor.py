from datetime import date
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session
from app import models, schemas
from app.crud import profile_image as crud_profile_image
from app.crud import patient as crud_patient

def get_doctor_profile(db: Session, user_id: int):
    """Fetch doctor profile"""
    return db.query(models.DoctorProfile).filter(models.DoctorProfile.DoctorID == user_id).first()


def create_or_update_doctor_profile(db: Session, user_id: int, data: schemas.DoctorProfileCreate):
    """Create or update doctor profile"""
    profile = db.query(models.DoctorProfile).filter(models.DoctorProfile.DoctorID == user_id).first()

    # Remove DoctorID if present (prevents multiple values error)
    data_dict = data.model_dump(exclude_unset=True)
    data_dict.pop("DoctorID", None)

    if profile:
        # Update existing profile
        for key, value in data_dict.items():
            setattr(profile, key, value)
    else:
        # Create new profile
        profile = models.DoctorProfile(DoctorID=user_id, **data_dict)
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


def delete_doctor_profile(db: Session, user_id: int):
    """Delete doctor profile"""
    profile = db.query(models.DoctorProfile).filter(models.DoctorProfile.DoctorID == user_id).first()
    if profile:
        db.delete(profile)
        db.commit()
        return True
    return False


def get_all_doctors(db: Session):
    """Fetch all doctors with basic user details"""
    return db.query(
        models.DoctorProfile.DProfilePhoto,
        models.User.UserID,
        models.User.FirstName,
        models.User.LastName,
        models.User.Phone,
        models.DoctorProfile.Specialization,
        models.DoctorProfile.ExperienceYears
    ).join(models.DoctorProfile, models.User.UserID == models.DoctorProfile.DoctorID).all()


def get_doctor_appointments(db: Session, doctor_id: int, query_date: date):
    """Fetch appointments for a specific doctor on a specific date"""
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
        .filter(
            models.Appointment.DoctorID == doctor_id,
            cast(models.Appointment.DateTime, Date) == query_date,
        )
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


def upload_or_update_doctor_profile_image(
    db: Session,
    doctor_id: int,
    file_name: str,
    file_bytes: bytes,
    content_type: str | None,
):
    return crud_profile_image.upsert_profile_image(
        db=db,
        user_id=doctor_id,
        role_type="doctor",
        file_name=file_name,
        file_bytes=file_bytes,
        content_type=content_type,
    )


def get_doctor_profile_image(db: Session, doctor_id: int):
    return crud_profile_image.get_profile_image_record(
        db=db,
        user_id=doctor_id,
        role_type="doctor",
    )


def get_doctor_profile_image_download_url(
    file_path: str,
    storage_bucket: str,
    expires_in_seconds: int = 600,
):
    return crud_profile_image.create_profile_image_download_url(
        storage_path=file_path,
        storage_bucket=storage_bucket,
        expires_in_seconds=expires_in_seconds,
    )


def upsert_consultation_for_doctor(
    db: Session,
    doctor_id: int,
    appointment_id: int,
    payload: schemas.ConsultationCreate,
):
    appointment = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.AppointmentID == appointment_id,
            models.Appointment.DoctorID == doctor_id,
        )
        .first()
    )
    if not appointment:
        raise ValueError("Appointment not found for this doctor.")

    consultation = (
        db.query(models.Consultation)
        .filter(models.Consultation.AppointmentID == appointment_id)
        .first()
    )

    if consultation:
        consultation.FollowUpRequired = payload.FollowUpRequired
        if payload.PrescriptionFile is not None:
            consultation.PrescriptionFile = payload.PrescriptionFile
    else:
        consultation = models.Consultation(
            AppointmentID=appointment_id,
            PrescriptionFile=payload.PrescriptionFile,
            FollowUpRequired=payload.FollowUpRequired,
        )
        db.add(consultation)

    db.commit()
    db.refresh(consultation)
    return consultation


def get_doctor_consultation_by_appointment(
    db: Session,
    doctor_id: int,
    appointment_id: int,
):
    appointment = (
        db.query(models.Appointment.AppointmentID)
        .filter(
            models.Appointment.AppointmentID == appointment_id,
            models.Appointment.DoctorID == doctor_id,
        )
        .first()
    )
    if not appointment:
        raise ValueError("Appointment not found for this doctor.")

    return (
        db.query(models.Consultation)
        .filter(models.Consultation.AppointmentID == appointment_id)
        .first()
    )


def get_doctor_prescription_download_url(
    db: Session,
    doctor_id: int,
    appointment_id: int,
    expires_in_seconds: int = 600,
):
    consultation = get_doctor_consultation_by_appointment(
        db=db,
        doctor_id=doctor_id,
        appointment_id=appointment_id,
    )
    if not consultation:
        raise ValueError("Consultation not found.")
    if not consultation.PrescriptionFile:
        raise ValueError("Prescription file not found.")

    download_url = crud_patient.create_document_download_url(
        storage_path=consultation.PrescriptionFile,
        expires_in_seconds=expires_in_seconds,
    )

    return {
        "AppointmentID": consultation.AppointmentID,
        "PrescriptionFile": consultation.PrescriptionFile,
        "DownloadURL": download_url,
        "ExpiresInSeconds": expires_in_seconds,
    }


def get_doctor_reports_by_appointment(
    db: Session,
    doctor_id: int,
    appointment_id: int,
):
    appointment = (
        db.query(models.Appointment.AppointmentID)
        .filter(
            models.Appointment.AppointmentID == appointment_id,
            models.Appointment.DoctorID == doctor_id,
        )
        .first()
    )
    if not appointment:
        raise ValueError("Appointment not found for this doctor.")

    return (
        db.query(models.Report)
        .join(models.InvestigationBooking, models.Report.BookingID == models.InvestigationBooking.BookingID)
        .filter(models.InvestigationBooking.AppointmentID == appointment_id)
        .order_by(models.Report.ReportID.desc())
        .all()
    )


def get_doctor_report_download_url(
    db: Session,
    doctor_id: int,
    document_id: int,
    expires_in_seconds: int = 600,
):
    report = (
        db.query(models.Report)
        .join(models.InvestigationBooking, models.Report.BookingID == models.InvestigationBooking.BookingID)
        .join(models.Appointment, models.InvestigationBooking.AppointmentID == models.Appointment.AppointmentID)
        .filter(
            models.Report.ReportID == document_id,
            models.Appointment.DoctorID == doctor_id,
        )
        .first()
    )
    if not report:
        raise ValueError("Report not found for this doctor.")

    download_url = crud_patient.create_document_download_url(
        storage_path=report.FilePath,
        expires_in_seconds=expires_in_seconds,
    )

    return {
        "DocumentID": report.DocumentID,
        "FileName": report.FileName,
        "FilePath": report.FilePath,
        "DownloadURL": download_url,
        "ExpiresInSeconds": expires_in_seconds,
    }
