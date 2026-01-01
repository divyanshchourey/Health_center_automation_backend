from datetime import date
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session
from app import models, schemas


def get_all_employees(db: Session):
    """Fetch all employees with basic user details"""
    return db.query(
        models.User.UserID,
        models.User.FirstName,
        models.User.LastName,
        models.User.Phone,
        models.Employee.Division,
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


def get_all_appointments_by_date(db: Session, query_date: date):
    """Fetch all appointments on a specific date"""
    appointments = db.query(models.Appointment).filter(
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


def delete_appointment(db: Session, appointment_id: int):
    """Delete an appointment by ID"""
    appointment = db.query(models.Appointment).filter(models.Appointment.AppointmentID == appointment_id).first()
    if appointment:
        db.delete(appointment)
        db.commit()
        return True
    return False
