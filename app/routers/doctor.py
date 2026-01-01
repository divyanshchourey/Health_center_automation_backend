from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.crud import doctor as crud_doctor

router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])

@router.get("/", response_model=list[schemas.DoctorListResponse])
def list_doctors(db: Session = Depends(get_db)):
    """List all doctors with basic details"""
    return crud_doctor.get_all_doctors(db)


@router.get("/{user_id}", response_model=schemas.DoctorProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = crud_doctor.get_doctor_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return profile


@router.post("/{user_id}")
def create_or_update_profile(user_id: int, data: schemas.DoctorProfileCreate, db: Session = Depends(get_db)):
    profile = crud_doctor.create_or_update_doctor_profile(db, user_id, data)
    return {"message": "Doctor profile saved successfully", "profile": profile}


@router.delete("/{user_id}")
def delete_profile(user_id: int, db: Session = Depends(get_db)):
    success = crud_doctor.delete_doctor_profile(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return {"message": "Doctor profile deleted"}


@router.get("/{user_id}/appointments", response_model=list[schemas.AppointmentEmployeeResponse])
def get_appointments(user_id: int, date: date, db: Session = Depends(get_db)):
    """Get appointments for a specific doctor on a specific date"""
    return crud_doctor.get_doctor_appointments(db, user_id, date)
