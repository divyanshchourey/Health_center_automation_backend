import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, schemas

def verify_changes():
    db = SessionLocal()
    try:
        # 1. Create a test user (Patient) if not exists
        patient_user = db.query(models.User).filter(models.User.Email == "test_patient@example.com").first()
        if not patient_user:
            patient_user = models.User(
                FirstName="Test",
                LastName="Patient",
                Email="test_patient@example.com",
                Phone="1234567890",
                Password="password",
                AadharNumber="123456789012",
                RoleID=3
            )
            db.add(patient_user)
            db.commit()
            db.refresh(patient_user)
            
            patient_profile = models.PatientProfile(PatientID=patient_user.UserID)
            db.add(patient_profile)
            db.commit()

        # 2. Create a test user (Doctor) if not exists
        doctor_user = db.query(models.User).filter(models.User.Email == "test_doctor@example.com").first()
        if not doctor_user:
            doctor_user = models.User(
                FirstName="Test",
                LastName="Doctor",
                Email="test_doctor@example.com",
                Phone="0987654321",
                Password="password",
                AadharNumber="210987654321",
                RoleID=2
            )
            db.add(doctor_user)
            db.commit()
            db.refresh(doctor_user)
            
            doctor_profile = models.DoctorProfile(DoctorID=doctor_user.UserID, Specialization="General Physician")
            db.add(doctor_profile)
            db.commit()

        # 3. Create a test appointment
        appt = models.Appointment(
            PatientID=patient_user.UserID,
            DoctorID=doctor_user.UserID,
            DateTime=datetime.utcnow() + timedelta(days=1),
            Type="General Checkup",
            Status="PENDING"
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)
        
        print(f"Created Appointment ID: {appt.AppointmentID}, Initial Status: {appt.Status}")

        # 4. Check status via CRUD logic (simulated)
        from app.crud import patient as crud_patient
        categorized = crud_patient.get_categorized_appointments(db, patient_user.UserID)
        found = False
        for a in categorized["upcoming"]:
            if a.AppointmentID == appt.AppointmentID:
                print(f"CRUD Status before billing: {a.Status}")
                found = True
                if a.Status != "PENDING":
                    print("Error: Status should be PENDING")
        
        if not found:
             print("Error: Appointment not found in categorized list")

        # 5. Create DoctorBilling entry
        bill = models.DoctorBilling(
            AppointmentID=appt.AppointmentID,
            Amount=Decimal("800.00"),
            Date=datetime.utcnow()
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        print(f"Created DoctorBilling entry for Appointment ID: {appt.AppointmentID}")

        # 6. Check status again
        db.expire_all() # Ensure we get fresh data
        categorized = crud_patient.get_categorized_appointments(db, patient_user.UserID)
        found = False
        for a in categorized["upcoming"]:
            if a.AppointmentID == appt.AppointmentID:
                print(f"CRUD Status after billing: {a.Status}, Method: {getattr(a, 'Method', 'N/A')}")
                found = True
                if a.Status == "Paid" and getattr(a, 'Method', '') == "Cash":
                    print("Success: Status is Paid and Method is Cash")
                else:
                    print(f"Error: Unexpected Status ({a.Status}) or Method ({getattr(a, 'Method', '')})")

        # 7. Test pay_doctor_bill bug fix
        payload = schemas.DoctorBillingCreate(
            AppointmentID=appt.AppointmentID,
            Amount=800.0,
            PaymentID=None
        )
        # Note: pay_doctor_bill usually takes a payload with Method
        mock_payload = type('obj', (object,), {'Method': 'Cash', 'TransactionRef': 'TXN123'})
        
        try:
            result = crud_patient.pay_doctor_bill(db, patient_user.UserID, appt.AppointmentID, mock_payload)
            print(f"pay_doctor_bill result: {result}")
            if result['PaymentID'] is not None:
                print("Success: pay_doctor_bill bug fixed and working")
        except Exception as e:
            print(f"Error in pay_doctor_bill: {e}")

    finally:
        # Cleanup
        # db.delete(bill) # Already might have payment
        # db.delete(appt)
        db.close()

if __name__ == "__main__":
    verify_changes()
