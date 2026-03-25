
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import schemas
from app.crud import admin as crud_admin
from app.crud import users as crud_users
import sys
import uuid

def verify():
    db = SessionLocal()
    try:
        # 1. Create a random email for the new owner to avoid collisions
        unique_suffix = str(uuid.uuid4())[:8]
        test_email = f"labowner_{unique_suffix}@test.com"
        test_password = "securepassword123"
        test_lab_name = f"Test Lab {unique_suffix}"

        # 2. Prepare payload
        payload = schemas.LabCenterCreate(
            Name=test_lab_name,
            Address="123 Test St",
            Contact="9998887776",
            AccreditationNumber="TEST-AC-123",
            ApprovedByAdmin=True,
            OwnerEmail=test_email,
            OwnerPassword=test_password,
            OwnerFirstName="Test",
            OwnerLastName="Owner",
            OwnerPhone="9998887776",
            OwnerAadharNumber=f"123456{unique_suffix[:6]}"
        )

        print(f"Attempting to create lab: {test_lab_name} with owner email: {test_email}")

        # 3. Call create_lab
        created_lab = crud_admin.create_lab(db, payload)
        
        print(f"Lab created with ID: {created_lab.LabID}")
        print(f"OwnerUserID attached: {created_lab.OwnerUserID}")

        if not created_lab.OwnerUserID:
            print("ERROR: OwnerUserID is None. The user wasn't linked properly.")
            sys.exit(1)

        # 4. Verify user was created
        owner_user = crud_users.get_user_by_id(db, created_lab.OwnerUserID)
        if not owner_user:
            print("ERROR: Could not find user by OwnerUserID.")
            sys.exit(1)

        print(f"Owner User found: {owner_user.FirstName} {owner_user.LastName} (RoleID: {owner_user.RoleID})")
        
        if owner_user.Email != test_email:
            print(f"ERROR: Email mismatch. Expected {test_email}, got {owner_user.Email}")
            sys.exit(1)

        if owner_user.RoleID != 5:
            print(f"ERROR: Role mismatch. Expected 5 (Lab), got {owner_user.RoleID}")
            sys.exit(1)

        # 5. Verify password works
        password_valid = crud_users.verify_password(test_password, owner_user.Password)
        if not password_valid:
            print("ERROR: Password verification failed.")
            sys.exit(1)
            
        print("Password verified successfully! Lab Owner can login.")
        
        # Cleanup (optional, but good for tests)
        db.delete(created_lab)
        db.delete(owner_user)
        db.commit()
        print("Test data cleaned up successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error during verification: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    verify()
