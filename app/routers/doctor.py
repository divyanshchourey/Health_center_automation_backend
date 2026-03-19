from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from datetime import date
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.crud import doctor as crud_doctor
from app.crud import employee as crud_employee
from app import models
from app.core.security import get_current_user

router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])

DOCTOR_ROLE_ID = 2


def _is_doctor_user(current_user: models.User) -> bool:
    role_name = (getattr(getattr(current_user, "role", None), "RoleName", "") or "").strip().lower()
    return current_user.RoleID == DOCTOR_ROLE_ID or role_name == "doctor"


@router.get("/", response_model=list[schemas.DoctorListResponse])
def list_doctors(db: Session = Depends(get_db)):
    """List all doctors with basic details"""
    return crud_doctor.get_all_doctors(db)


@router.post("/profile-image")
async def upload_update_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not _is_doctor_user(current_user):
        raise HTTPException(status_code=403, detail="Only doctor can upload profile image")
    
    file_bytes = await file.read()

    try:
        return crud_doctor.upload_or_update_doctor_profile_image(
            db= db,
            doctor_id= current_user.UserID,
            file_name= file.filename or "profile.jpg",
            file_bytes= file_bytes,
            content_type= file.content_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.put("/profile-image")
async def update_profile_image (
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await upload_update_profile_image(file=file, db=db, current_user = current_user)

@router.get("/profile-image")
def get_my_profile_image(
    expires_in_seconds: int = Query(default=600, ge=60, le=86400),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_doctor_user(current_user):
        raise HTTPException(status_code=403, detail="Only doctor can access profile image")

    image = crud_doctor.get_doctor_profile_image(db=db, doctor_id=current_user.UserID)
    if not image:
        raise HTTPException(status_code=404, detail="Profile image not found")

    try:
        download_url = crud_doctor.get_doctor_profile_image_download_url(
            file_path=image.FilePath,
            storage_bucket=image.StorageBucket,
            expires_in_seconds=expires_in_seconds,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "ImageID": image.ImageID,
        "FileName": image.FileName,
        "FilePath": image.FilePath,
        "DownloadURL": download_url,
        "ExpiresInSeconds": expires_in_seconds,
    }


@router.get("/{user_id}", response_model=schemas.DoctorProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = crud_doctor.get_doctor_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return profile


@router.post("/{user_id}", response_model=schemas.DoctorProfileResponse)
def create_or_update_profile(user_id: int, data: schemas.DoctorProfileCreate, db: Session = Depends(get_db)):
    return crud_doctor.create_or_update_doctor_profile(db, user_id, data)


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

@router.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    success = crud_employee.delete_appointment(db, appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted successfully"}

@router.post("/appointments/{appointment_id}/consultation", response_model=schemas.ConsultationResponse)
def create_or_update_consultation(
    appointment_id: int,
    payload: schemas.ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_doctor_user(current_user):
        raise HTTPException(status_code=403, detail="Only doctor can update consultation")
    if payload.AppointmentID != appointment_id:
        raise HTTPException(status_code=400, detail="AppointmentID in body must match URL.")
    try:
        return crud_doctor.upsert_consultation_for_doctor(
            db=db,
            doctor_id=current_user.UserID,
            appointment_id=appointment_id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/appointments/{appointment_id}/consultation", response_model=schemas.ConsultationResponse)
def get_consultation_by_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_doctor_user(current_user):
        raise HTTPException(status_code=403, detail="Only doctor can view consultation")
    try:
        consultation = crud_doctor.get_doctor_consultation_by_appointment(
            db=db,
            doctor_id=current_user.UserID,
            appointment_id=appointment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return consultation
