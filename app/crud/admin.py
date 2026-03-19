from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]
from sqlalchemy import func

from app import models, schemas
from app.crud import patient as crud_patient
from datetime import date, datetime


def create_lab(db: Session, payload: schemas.LabCenterCreate):
    lab = models.LabCenter(
        Name=payload.Name,
        Address=payload.Address,
        Contact=payload.Contact,
        AccreditationNumber=payload.AccreditationNumber,
        ApprovedByAdmin=bool(payload.ApprovedByAdmin),
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return lab


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


def list_admin_appointments(db: Session, query_date: date | None = None):
    query = (
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
    )

    if query_date is not None:
        query = query.filter(cast(models.Appointment.DateTime, Date) == query_date)

    appointments = query.order_by(models.Appointment.DateTime.desc()).all()

    results = []
    for appt in appointments:
        patient_name = f"{appt.PatientFirstName or ''} {appt.PatientLastName or ''}".strip() or "Unknown"
        doctor_name = "Unknown"
        doctor_user = db.query(models.User).filter(models.User.UserID == appt.DoctorID).first()
        if doctor_user:
            doctor_name = f"{doctor_user.FirstName} {doctor_user.LastName or ''}".strip() or "Unknown"

        results.append(
            schemas.AppointmentEmployeeResponse(
                AppointmentID=appt.AppointmentID,
                PatientID=appt.PatientID,
                PatientName=patient_name,
                DoctorID=appt.DoctorID,
                DoctorName=doctor_name,
                DateTime=appt.DateTime,
                Type=appt.Type,
                Status=appt.Status,
            )
        )

    return results