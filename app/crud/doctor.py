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
