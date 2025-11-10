from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.crud import patient as crud_patient

router = APIRouter(prefix="/patient", tags=["Patient Dashboard"])


@router.get("/{user_id}", response_model=schemas.PatientProfileResponse)
def get_patient_profile(user_id: int, db: Session = Depends(get_db)):
    profile = crud_patient.get_patient_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return profile


@router.post("/{user_id}", response_model=schemas.PatientProfileResponse)
def create_or_update_patient_profile(user_id: int, data: schemas.PatientProfileCreate, db: Session = Depends(get_db)):
    profile = crud_patient.create_or_update_patient_profile(db, user_id, data)
    return profile


@router.delete("/{user_id}")
def delete_patient_profile(user_id: int, db: Session = Depends(get_db)):
    success = crud_patient.delete_patient_profile(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return {"message": "Patient profile deleted successfully"}

@router.post("/appointment", response_model=schemas.AppointmentResponse)
def create_appointment(data: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    try:
        appointment = crud_patient.create_appointment(db, data)
        return appointment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))