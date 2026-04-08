import sys
import os
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, schemas

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def verify_changes():
    db = SessionLocal()
    try:
        # Create a unique test patient
        uid = random_string(5)
        patient_email = f"test_patient_{uid}@example.com"
        aadhar = "".join(random.choices(string.digits, k=12))
        
        patient_user = models.User(
            FirstName="Test",
            LastName="Patient",
            Email=patient_email,
            Phone=random_string(10),
            Password="password",
            AadharNumber=aadhar,
            RoleID=3
        )
        db.add(patient_user)
        db.commit()
        db.refresh(patient_user)
        
        patient_profile = models.PatientProfile(PatientID=patient_user.UserID)
        db.add(patient_profile)
        db.commit()

        # Create a unique test doctor
        doctor_email = f"test_doctor_{uid}@example.com"
        doctor_aadhar = "".join(random.choices(string.digits, k=12))
        
        doctor_user = models.User(
            FirstName="Test",
            LastName="Doctor",
            Email=doctor_email,
            Phone=random_string(10),
            Password="password",
            AadharNumber=doctor_aadhar,
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

        # 4. Check status via CRUD logic
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
        db.expire_all()
        # Fresh fetch
        categorized = crud_patient.get_categorized_appointments(db, patient_user.UserID)
        found = False
        for a in categorized["upcoming"]:
            if a.AppointmentID == appt.AppointmentID:
                method = getattr(a, 'Method', 'N/A')
                print(f"CRUD Status after billing: {a.Status}, Method: {method}")
                found = True
                if a.Status == "Paid" and method == "Cash":
                    print("Success: Status is Paid and Method is Cash")
                else:
                    print(f"Error: Unexpected Status ({a.Status}) or Method ({method})")

        # 7. Test pay_doctor_bill bug fix
        # Create a second appointment for payment test
        appt2 = models.Appointment(
            PatientID=patient_user.UserID,
            DoctorID=doctor_user.UserID,
            DateTime=datetime.utcnow() + timedelta(days=2),
            Type="General Checkup",
            Status="PENDING"
        )
        db.add(appt2)
        db.commit()
        db.refresh(appt2)
        
        # Test payment logic (which should fetch/create bill)
        mock_payload = type('obj', (BaseModel,), {'Method': 'Cash', 'TransactionRef': 'TXN123'})
        class MockPayload:
             Method = "Cash"
             TransactionRef = "TXN123"
        
        try:
            result = crud_patient.pay_doctor_bill(db, patient_user.UserID, appt2.AppointmentID, MockPayload())
            print(f"pay_doctor_bill result: {result}")
            if result['PaymentID'] is not None:
                print("Success: pay_doctor_bill bug fixed and working")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error in pay_doctor_bill: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    from pydantic import BaseModel
    verify_changes()
