from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.database import get_db
from app.crud import employee as crud_employee

router = APIRouter(prefix="/employee", tags=["Employee"])

@router.get("/{user_id}", response_model=schemas.EmployeeResponse)
def get_employee_profile(user_id: int, db: Session = Depends(get_db)):
    profile = crud_employee.get_employee_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return profile


@router.post("/{user_id}", response_model=schemas.EmployeeResponse)
def create_or_update_employee_profile(user_id: int, data: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    return crud_employee.create_or_update_employee_profile(db, user_id, data)


@router.delete("/{user_id}")
def delete_employee_profile(user_id: int, db: Session = Depends(get_db)):
    success = crud_employee.delete_employee_profile(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return {"message": "Employee profile deleted successfully"}


@router.get("/appointments/today", response_model=list[schemas.AppointmentResponse])
def todays_appointments(db: Session = Depends(get_db)):
    return crud_employee.get_todays_appointments(db)