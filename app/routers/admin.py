from fastapi import APIRouter, Depends, HTTPException, Query, status  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]
from datetime import date, datetime
from app import models, schemas
from app.core.security import get_current_user
from app.crud import lab as crud_lab
from app.crud import patient as crud_patient
from app.crud import doctor as crud_doctor
from app.crud import admin as crud_admin
from app.core.dependencies import require_role
from app.database import get_db

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/patients", response_model=list[schemas.PatientListResponse])
def list_patients(db: Session = Depends(get_db)):
    """List all patients with basic details"""
    return crud_patient.get_all_patients(db)

@router.get("/doctors", response_model =list[schemas.DoctorListResponse])
def list_doctors(db: Session=Depends(get_db)):
    """ List of Doctors"""
    return crud_doctor.get_all_doctors(db)

@router.get("/labcenters", response_model=list[schemas.LabCenterResponse])
def list_of_labcenters(db: Session=Depends(get_db)):
    return crud_lab.list_labs(db)



@router.post("/add labs", response_model=schemas.LabCenterResponse)
def add_lab_by_admin(
    payload: schemas.LabCenterCreate,
    db: Session = Depends(get_db),
):
    try:
        return crud_admin.create_lab(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/labcenters/{lab_id}", response_model=schemas.LabCenterResponse)
def get_lab_center(lab_id: int, db: Session = Depends(get_db)):
    lab = crud_admin.get_lab_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab center not found")
    return lab


@router.put("/labcenters/{lab_id}", response_model=schemas.LabCenterResponse)
def update_lab_center(lab_id: int, payload: schemas.LabCenterCreate, db: Session = Depends(get_db)):
    lab = crud_admin.update_lab(db, lab_id, payload)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab center not found")
    return lab


@router.delete("/labcenters/{lab_id}")
def delete_lab_center(lab_id: int, db: Session = Depends(get_db)):
    success = crud_admin.delete_lab(db, lab_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lab center not found")
    return {"message": "Lab center deleted successfully"}

@router.get("/appointments", response_model=list[schemas.AppointmentEmployeeResponse])
def list_admin_appointments(
    date: date | None = None,
    db: Session = Depends(get_db),
):
    return crud_admin.list_admin_appointments(db=db, query_date=date)
