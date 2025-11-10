from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas
from app.database import get_db
from app.crud import users as crud_users

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ----------------------------
# Register User
# ----------------------------
@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user = crud_users.get_user_by_email(db, user.Email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = crud_users.create_user(db, user)
    return new_user


# ----------------------------
# Login User
# ----------------------------
@router.post("/login")
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login user by verifying credentials"""
    user = crud_users.get_user_by_email(db, credentials.Email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not crud_users.verify_password(credentials.Password, user.Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    return {
        "message": "Login successful",
        "user": {
            "UserID": user.UserID,
            "FirstName": user.FirstName,
            "LastName": user.LastName,
            "Email": user.Email,
            "Phone": user.Phone,
            "RoleID": user.RoleID
        }
    }


# ----------------------------
# Patient Login (RoleID = 3)
# ----------------------------
@router.post("/login/patient")
def login_patient(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login patient by verifying credentials and roleID=3"""
    user = crud_users.get_user_by_email(db, credentials.Email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not crud_users.verify_password(credentials.Password, user.Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Verify that the user is a patient (RoleID = 3)
    if user.RoleID != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint is only for patients."
        )

    return {
        "message": "Patient login successful",
        "user": {
            "UserID": user.UserID,
            "FirstName": user.FirstName,
            "LastName": user.LastName,
            "Email": user.Email,
            "Phone": user.Phone,
            "RoleID": user.RoleID
        }
    }

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    success = crud_users.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User with ID {user_id} deleted successfully"}

@router.get("/user/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get only the user table details"""
    user = crud_users.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user