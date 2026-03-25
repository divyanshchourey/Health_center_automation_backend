
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import schemas, models
from app.crud import admin as crud_admin
from app.crud import users as crud_users
from app.core.security import create_access_token
import uuid
import sys

client = TestClient(app)

def verify():
    db = SessionLocal()
    try:
        # Create Lab 1 and Owner 1
        u1 = str(uuid.uuid4())[:8]
        payload1 = schemas.LabCenterCreate(
            Name=f"Lab A {u1}", Address="123", Contact="999", AccreditationNumber="A123",
            ApprovedByAdmin=True, OwnerEmail=f"o1_{u1}@test.com", OwnerPassword="pw",
            OwnerFirstName="O1", OwnerLastName="L1", OwnerPhone="111", OwnerAadharNumber=f"A1{u1}"
        )
        lab1 = crud_admin.create_lab(db, payload1)
        owner1 = crud_users.get_user_by_id(db, lab1.OwnerUserID)
        token1 = create_access_token({"sub": str(owner1.UserID), "role_id": owner1.RoleID})

        # Create Lab 2 and Owner 2
        u2 = str(uuid.uuid4())[:8]
        payload2 = schemas.LabCenterCreate(
            Name=f"Lab B {u2}", Address="456", Contact="888", AccreditationNumber="B456",
            ApprovedByAdmin=True, OwnerEmail=f"o2_{u2}@test.com", OwnerPassword="pw",
            OwnerFirstName="O2", OwnerLastName="L2", OwnerPhone="222", OwnerAadharNumber=f"B2{u2}"
        )
        lab2 = crud_admin.create_lab(db, payload2)
        owner2 = crud_users.get_user_by_id(db, lab2.OwnerUserID)
        token2 = create_access_token({"sub": str(owner2.UserID), "role_id": owner2.RoleID})
        
        # Admin Token (Assuming admin is role 1, we can just create a temp admin)
        admin_create = schemas.UserCreate(
            FirstName="Admin", LastName="Test", Email=f"admin_{u1}@test.com", Phone="000",
            Password="pw", AadharNumber=f"ADM{u1}", RoleID=1
        )
        admin_user = crud_users.create_user(db, admin_create)
        token_admin = create_access_token({"sub": str(admin_user.UserID), "role_id": admin_user.RoleID})

        print("--- Testing Lab Owner 1 ---")
        # Owner 1 accessing Lab 1 (Should Succeed)
        res = client.get(f"/lab/{lab1.LabID}/bookings", headers={"Authorization": f"Bearer {token1}"})
        if res.status_code != 200:
            print(f"FAILED: Owner 1 could not access Lab 1. Code: {res.status_code}, Detail: {res.text}")
            sys.exit(1)
        print("PASS: Owner 1 can access Lab 1")

        # Owner 1 accessing Lab 2 (Should Fail with 403)
        res = client.get(f"/lab/{lab2.LabID}/bookings", headers={"Authorization": f"Bearer {token1}"})
        if res.status_code != 403:
            print(f"FAILED: Owner 1 accessed Lab 2 improperly. Code: {res.status_code}")
            sys.exit(1)
        print("PASS: Owner 1 is forbidden from accessing Lab 2")

        print("--- Testing Lab Owner 2 ---")
        # Owner 2 accessing Lab 2 (Should Succeed)
        res = client.get(f"/lab/{lab2.LabID}/bookings", headers={"Authorization": f"Bearer {token2}"})
        if res.status_code != 200:
            print(f"FAILED: Owner 2 could not access Lab 2. Code: {res.status_code}")
            sys.exit(1)
        print("PASS: Owner 2 can access Lab 2")

        print("--- Testing Admin ---")
        # Admin accessing Lab 1 (Should Succeed)
        res = client.get(f"/lab/{lab1.LabID}/bookings", headers={"Authorization": f"Bearer {token_admin}"})
        if res.status_code != 200:
            print(f"FAILED: Admin could not access Lab 1. Code: {res.status_code}, Detail: {res.text}")
            sys.exit(1)
        print("PASS: Admin can access Lab 1")
        
        # Test Query Param Injection
        res = client.get(f"/lab/investigations?lab_id={lab1.LabID}", headers={"Authorization": f"Bearer {token1}"})
        if res.status_code != 200:
            print(f"FAILED: Owner 1 could not access investigations list. Code: {res.status_code}")
            sys.exit(1)
        print("PASS: Owner 1 can access investigations via query parameter lab_id")

        print("ALL TESTS PASSED!")

        # Cleanup
        db.delete(lab1)
        db.delete(lab2)
        db.delete(owner1)
        db.delete(owner2)
        db.delete(admin_user)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error during verification: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    verify()
