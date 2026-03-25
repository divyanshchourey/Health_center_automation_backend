from datetime import datetime, timedelta
from app.database import SessionLocal
from app.crud.patient import create_appointment_for_patient
from app import schemas, models

def test_double_booking():
    db = SessionLocal()
    try:
        doctor_id = 59  
        patient_a_id = 22  
        patient_b_id = 24  
        
        # Unique time for testing
        test_time = datetime.utcnow() + timedelta(days=1, hours=10)
        # Avoid microseconds as they might cause mismatch depending on how DB stores them
        test_time = test_time.replace(microsecond=0)
        
        print(f"Testing for time: {test_time}")
        
        # 1. Book first appointment
        payload_a = schemas.AppointmentCreate(
            PatientID=patient_a_id,
            DoctorID=doctor_id,
            DateTime=test_time,
            Type="consultation",
            Status="PENDING"
        )
        
        print(f"Creating first appointment for Patient {patient_a_id}...")
        appt_a = create_appointment_for_patient(db, patient_a_id, payload_a)
        print(f"First appointment created: ID {appt_a.AppointmentID}")
        
        # 2. Attempt to book second appointment for same doctor and same time
        payload_b = schemas.AppointmentCreate(
            PatientID=patient_b_id,
            DoctorID=doctor_id,
            DateTime=test_time,
            Type="consultation",
            Status="PENDING"
        )
        
        print(f"Attempting to create second appointment for Patient {patient_b_id} at the same time...")
        try:
            create_appointment_for_patient(db, patient_b_id, payload_b)
            print("ERROR: Double booking was allowed!")
        except ValueError as e:
            print(f"SUCCESS: Caught expected error: {e}")
            
        # Cleanup
        db.delete(appt_a)
        db.commit()
        print("Test appointment cleaned up.")
        
    finally:
        db.close()

if __name__ == '__main__':
    test_double_booking()
