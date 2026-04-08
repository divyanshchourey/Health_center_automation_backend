import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app import models, schemas
from pydantic import ValidationError

def test_models():
    print("Testing models properties...")
    user = models.User(UserID=1, FirstName="John", LastName="Doe", AadharNumber="1234-5678-9012")
    
    patient = models.PatientProfile(PatientID=1, user=user)
    doctor = models.DoctorProfile(DoctorID=2, user=user)
    employee = models.Employee(EmployeeID=3, user=user)
    
    print(f"Patient Aadhar: {patient.AadharNumber}")
    assert patient.AadharNumber == "1234-5678-9012"
    
    print(f"Doctor Aadhar: {doctor.AadharNumber}")
    assert doctor.AadharNumber == "1234-5678-9012"
    
    print(f"Employee Aadhar: {employee.AadharNumber}")
    assert employee.AadharNumber == "1234-5678-9012"
    print("Models properties verified!\n")

def test_schemas():
    print("Testing schemas...")
    
    # Test PatientProfileResponse
    data = {"PatientID": 1, "AadharNumber": "1234-5678-9012", "BloodGroup": "O+"}
    p_resp = schemas.PatientProfileResponse(**data)
    print(f"PatientProfileResponse: {p_resp.model_dump()}")
    assert p_resp.AadharNumber == "1234-5678-9012"
    
    # Test DoctorProfileResponse
    data = {"DoctorID": 2, "AadharNumber": "1234-5678-9012", "Specialization": "General"}
    d_resp = schemas.DoctorProfileResponse(**data)
    print(f"DoctorProfileResponse: {d_resp.model_dump()}")
    assert d_resp.AadharNumber == "1234-5678-9012"
    
    # Test EmployeeResponse
    data = {"EmployeeID": 3, "AadharNumber": "1234-5678-9012", "Designation": "Staff"}
    e_resp = schemas.EmployeeResponse(**data)
    print(f"EmployeeResponse: {e_resp.model_dump()}")
    assert e_resp.AadharNumber == "1234-5678-9012"
    
    print("Schemas verified!\n")

if __name__ == "__main__":
    try:
        test_models()
        test_schemas()
        print("ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
        sys.exit(1)
