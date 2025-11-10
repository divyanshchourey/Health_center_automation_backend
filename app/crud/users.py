from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import models, schemas
from datetime import datetime

# Using Argon2 for hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# -------- Password helpers --------
def hash_password(password: str):
    """Hash the password using Argon2."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verify a plain password against the stored Argon2 hash.

    Be defensive: if the stored hash is in an unknown format or the
    Argon2 backend isn't available, return False instead of raising.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Unknown hash format or missing backend; treat as invalid credentials
        return False

# -------- CRUD Operations --------
def get_user_by_email(db: Session, email: str):
    """Fetch a user by email."""
    return db.query(models.User).filter(models.User.Email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user with a hashed password."""
    hashed_pw = hash_password(user.Password)
    db_user = models.User(
        FirstName=user.FirstName,
        LastName=user.LastName,
        Email=user.Email,
        Phone=user.Phone,
        Password=hashed_pw,
        RoleID=user.RoleID,
        Gender=user.Gender,
        DOB=user.DOB,
        Address=user.Address,
        CreatedAt=datetime.utcnow(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    """Delete a user and related profiles (employee/doctor/patient)"""
    user = db.query(models.User).filter(models.User.UserID == user_id).first()

    if not user:
        return False

    # Delete related profiles (optional, if not using cascade delete)
    if user.employee:
        db.delete(user.employee)
    if hasattr(user, "doctor") and user.doctor:
        db.delete(user.doctor)
    if hasattr(user, "patient") and user.patient:
        db.delete(user.patient)

    # Finally delete the user
    db.delete(user)
    db.commit()
    return True

def get_user_by_id(db: Session, user_id: int):
    """Fetch only the user table details by UserID."""
    return db.query(models.User).filter(models.User.UserID == user_id).first()