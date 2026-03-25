
import sys
from unittest.mock import MagicMock

# Mock supabase to avoid dependency issues during testing
mock_supabase = MagicMock()
sys.modules["supabase"] = mock_supabase
sys.modules["supabase.client"] = MagicMock()

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import schemas, models
from app.crud import admin as crud_admin
from app.crud import users as crud_users
from app.crud import lab as crud_lab
from app.core.security import create_access_token
import uuid
from datetime import datetime

client = TestClient(app)

def verify():
    db = SessionLocal()
    try:
        # 1. Create a Lab and Owner
        u_suffix = str(uuid.uuid4())[:8]
        lab_payload = schemas.LabCenterCreate(
            Name=f"Test Lab {u_suffix}", Address="Test Addr", Contact="123456", AccreditationNumber="ACC123",
            ApprovedByAdmin=True, OwnerEmail=f"lab_{u_suffix}@test.com", OwnerPassword="password",
            OwnerFirstName="Lab", OwnerLastName="Owner", OwnerPhone=f"P1{u_suffix}", OwnerAadharNumber=f"A1{u_suffix}"
        )
        lab = crud_admin.create_lab(db, lab_payload)
        owner = crud_users.get_user_by_id(db, lab.OwnerUserID)
        owner_token = create_access_token({"sub": str(owner.UserID), "role_id": owner.RoleID})

        # 2. Create an Investigation (Test)
        investigation_payload = schemas.InvestigationCreate(
            Name=f"Test Investigation {u_suffix}",
            Description="Description",
            DefaultRate=100.0
        )
        investigation = crud_lab.create_investigation(db, investigation_payload)

        # 3. Create a Patient
        patient_payload = schemas.UserCreate(
            FirstName="John", LastName="Doe", Email=f"patient_{u_suffix}@test.com", Phone=f"P2{u_suffix}",
            Password="password", AadharNumber=f"A2{u_suffix}", RoleID=3
        )
        patient_user = crud_users.create_user(db, patient_payload)
        
        # Create PatientProfile (necessary for relationships)
        patient_profile = models.PatientProfile(PatientID=patient_user.UserID)
        db.add(patient_profile)
        db.commit()
        
        # 4. Create an Appointment
        appointment = models.Appointment(
            PatientID=patient_user.UserID,
            DateTime=datetime.utcnow(),
            Type="Lab",
            Status="PENDING",
            LabID=lab.LabID
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        # 5. Create a Booking
        booking_payload = schemas.InvestigationBookingCreate(
            AppointmentID=appointment.AppointmentID,
            InvestigationID=investigation["InvestigationID"],
            LabID=lab.LabID
        )
        booking = crud_lab.create_booking(db, patient_user.UserID, booking_payload)

        # 6. Call the endpoint and check the response
        print(f"--- Testing Lab Bookings for Lab ID: {lab.LabID} ---")
        headers = {"Authorization": f"Bearer {owner_token}"}
        response = client.get(f"/lab/{lab.LabID}/bookings", headers=headers)
        
        if response.status_code != 200:
            print(f"FAILED: Could not fetch bookings. Code: {response.status_code}, Detail: {response.text}")
            sys.exit(1)
            
        bookings = response.json()
        if not bookings:
            print("FAILED: No bookings returned.")
            sys.exit(1)
            
        test_booking = bookings[0]
        print(f"Booking response: {test_booking}")
        
        # Verify PatientName and InvestigationName
        expected_patient_name = "John Doe"
        expected_investigation_name = f"Test Investigation {u_suffix}"
        
        if test_booking.get("PatientName") != expected_patient_name:
            print(f"FAILED: PatientName mismatch. Expected '{expected_patient_name}', got '{test_booking.get('PatientName')}'")
            sys.exit(1)
            
        if test_booking.get("InvestigationName") != expected_investigation_name:
            print(f"FAILED: InvestigationName mismatch. Expected '{expected_investigation_name}', got '{test_booking.get('InvestigationName')}'")
            sys.exit(1)
            
        print("PASS: PatientName and InvestigationName are correctly returned in the response.")

        # Cleanup
        db.delete(booking)
        db.delete(appointment)
        db.delete(patient_profile)
        db.delete(patient_user)
        # Investigation and Lab might have other relations, but for this test we'll try to delete
        # Investigation was returned as a dict from crud_lab.create_investigation
        inv_obj = db.query(models.Investigation).filter(models.Investigation.InvestigationID == investigation["InvestigationID"]).first()
        if inv_obj:
            db.delete(inv_obj)
        db.delete(lab)
        db.delete(owner)
        db.commit()

        print("ALL TESTS PASSED!")

    except Exception as e:
        db.rollback()
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    verify()
