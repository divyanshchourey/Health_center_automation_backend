from sqlalchemy.orm import Session
from app import models, schemas

def get_patient_profile(db: Session, user_id: int):
    """Fetch patient profile"""
    return db.query(models.PatientProfile).filter(models.PatientProfile.PatientID == user_id).first()


def create_or_update_patient_profile(db: Session, user_id: int, data: schemas.PatientProfileCreate):
    """Create or update patient profile"""
    profile = db.query(models.PatientProfile).filter(models.PatientProfile.PatientID == user_id).first()

    # Remove PatientID from data if it exists (prevents duplicate key error)
    data_dict = data.model_dump(exclude_unset=True)
    data_dict.pop("PatientID", None)

    if profile:
        # Update existing profile
        for key, value in data_dict.items():
            setattr(profile, key, value)
    else:
        # Create new profile
        profile = models.PatientProfile(PatientID=user_id, **data_dict)
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


def delete_patient_profile(db: Session, user_id: int):
    """Delete patient profile"""
    profile = db.query(models.PatientProfile).filter(models.PatientProfile.PatientID == user_id).first()
    if profile:
        db.delete(profile)
        db.commit()
        return True
    return False

def create_appointment(db: Session, data: schemas.AppointmentCreate):
    """Create a new appointment"""
    # Optional: check if patient and doctor exist
    patient = db.query(models.User).filter(models.User.UserID == data.PatientID).first()
    doctor = db.query(models.User).filter(models.User.UserID == data.DoctorID).first()
    if not patient or not doctor:
        raise ValueError("Patient or Doctor does not exist")

    appointment = models.Appointment(**data.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment