from datetime import date
from sqlalchemy.orm import Session
from app import models, schemas

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

    # Join Appointments with DoctorProfile and PatientProfile to get UserIDs
    appointments = (
        db.query(
            models.Appointment.AppointmentID,
            models.Appointment.DoctorID,
            models.Appointment.PatientID,
            models.Appointment.AppointmentDate,
            models.Appointment.Time,
            models.DoctorProfile.user.label("DoctorUserID"),
            models.PatientProfile.user.label("PatientUserID")
        )
        .join(models.DoctorProfile, models.Appointment.DoctorID == models.DoctorProfile.DoctorID)
        .join(models.PatientProfile, models.Appointment.PatientID == models.PatientProfile.PatientID)
        .filter(models.Appointment.AppointmentDate == today)
        .all()
    )

    # Convert IDs to full names
    result = []
    for appt in appointments:
        doctor_user = db.query(models.User).filter(models.User.UserID == appt.DoctorUserID).first()
        patient_user = db.query(models.User).filter(models.User.UserID == appt.PatientUserID).first()
        result.append({
            "AppointmentID": appt.AppointmentID,
            "DoctorID": appt.DoctorID,
            "DoctorName": f"{doctor_user.FirstName} {doctor_user.LastName}" if doctor_user else None,
            "PatientID": appt.PatientID,
            "PatientName": f"{patient_user.FirstName} {patient_user.LastName}" if patient_user else None,
            "AppointmentDate": appt.AppointmentDate,
            "AppointmentTime": appt.Time,
        })
    return result
