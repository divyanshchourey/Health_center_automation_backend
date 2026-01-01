from datetime import date
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session
from app import models, schemas

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
        models.User.UserID,
        models.User.FirstName,
        models.User.LastName,
        models.User.Phone,
        models.DoctorProfile.Specialization,
        models.DoctorProfile.ExperienceYears
    ).join(models.DoctorProfile, models.User.UserID == models.DoctorProfile.DoctorID).all()


def get_doctor_appointments(db: Session, doctor_id: int, query_date: date):
    """Fetch appointments for a specific doctor on a specific date"""
    appointments = db.query(models.Appointment).filter(
        models.Appointment.DoctorID == doctor_id,
        cast(models.Appointment.DateTime, Date) == query_date
    ).all()

    results = []
    for appt in appointments:
        patient_name = "Unknown"
        if appt.patient and appt.patient.user:
            patient_name = f"{appt.patient.user.FirstName} {appt.patient.user.LastName}".strip()

        doctor_name = "Unknown"
        if appt.doctor and appt.doctor.user:
            doctor_name = f"{appt.doctor.user.FirstName} {appt.doctor.user.LastName}".strip()

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
