from datetime import date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from app import models, schemas
from app.core.security import get_current_user
from app.crud import employee as crud_employee
from app.crud import patient as crud_patient
from app.database import get_db

router = APIRouter(prefix="/employee", tags=["Employee"])

EMPLOYEE_ROLE_ID = 4


def _is_employee_user(current_user: models.User) -> bool:
    role_name = (getattr(getattr(current_user, "role", None), "RoleName", "") or "").strip().lower()
    return current_user.RoleID == EMPLOYEE_ROLE_ID or role_name == "employee"


@router.get("/", response_model=list[schemas.EmployeeListResponse])
def list_employees(db: Session = Depends(get_db)):
    return crud_employee.get_all_employees(db)


@router.get("/appointments/today", response_model=list[schemas.AppointmentResponse])
def todays_appointments(db: Session = Depends(get_db)):
    return crud_employee.get_todays_appointments(db)


@router.get("/appointments", response_model=list[schemas.AppointmentEmployeeResponse])
def get_appointments_by_date(date: date, db: Session = Depends(get_db)):
    return crud_employee.get_all_appointments_by_date(db, date)


@router.post("/profile-image")
async def upload_or_update_my_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only employee can upload profile image")

    file_bytes = await file.read()
    try:
        return crud_employee.upload_or_update_employee_profile_image(
            db=db,
            employee_id=current_user.UserID,
            file_name=file.filename or "profile.jpg",
            file_bytes=file_bytes,
            content_type=file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/profile-image")
async def update_my_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await upload_or_update_my_profile_image(file=file, db=db, current_user=current_user)


@router.get("/profile-image")
def get_my_profile_image(
    expires_in_seconds: int = Query(default=600, ge=60, le=86400),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only employee can access profile image")

    image = crud_employee.get_employee_profile_image(db=db, employee_id=current_user.UserID)
    if not image:
        raise HTTPException(status_code=404, detail="Profile image not found")

    try:
        download_url = crud_employee.get_employee_profile_image_download_url(
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


@router.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    success = crud_employee.delete_appointment(db, appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted successfully"}


@router.get("/doctor-bills/categories", response_model=list[schemas.DoctorBillingResponse])
def list_doctor_bill_categories(current_user: models.User = Depends(get_current_user)):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only employee can access bill categories")

    categories = crud_employee.get_doctor_checkup_price_list()

    result = []
    for index, item in enumerate(categories, start=1):
        result.append({
            "AppointmentID": 0,
            "PaymentID": 0,
            "Amount": item["Amount"],
            "DBillID": index,
            "Date": datetime.utcnow()
        })

    return result



@router.get("/doctor-bills/{appointment_id}", response_model=schemas.DoctorBillingResponse)
def get_doctor_bill(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only employee can access doctor bill")
    bill = crud_employee.get_doctor_bill_by_appointment(db=db, appointment_id=appointment_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Doctor bill not found")
    return bill


@router.post("/doctor-bills/{appointment_id}", response_model=schemas.DoctorBillingResponse)
def generate_doctor_bill(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only employee can generate doctor bill")

    try:
        return crud_employee.generate_doctor_bill(
            db=db,
            appointment_id=appointment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/doctor-bills/{appointment_id}/pay", response_model=schemas.PaymentResponse)
def pay_doctor_bill_by_employee(
    appointment_id: int,
    payload: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only employee can record doctor bill payment")

    try:
        return crud_employee.record_doctor_bill_payment(
            db=db,
            appointment_id=appointment_id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/appointments/{appointment_id}/prescription")
async def employee_upload_prescription(
    appointment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only staff can upload prescriptions")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF size exceeds 5 MB limit")

    try:
        saved = crud_patient.upload_consultation_prescription(
            db=db,
            appointment_id=appointment_id,
            file_name=file.filename or "prescription.pdf",
            pdf_bytes=file_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": "Prescription uploaded successfully",
        "consultation_id": saved["consultation_id"],
        "appointment_id": saved["appointment_id"],
        "path": saved["path"],
    }


@router.get("/bookings/{booking_id}/reports", response_model=list[schemas.ReportResponse])
def employee_list_booking_reports(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only staff can access reports")
    try:
        return crud_patient.list_reports_by_booking(db=db, booking_id=booking_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reports/{document_id}/download")
def employee_download_booking_report(
    document_id: int,
    expires_in_seconds: int = Query(default=600, ge=60, le=86400),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not _is_employee_user(current_user):
        raise HTTPException(status_code=403, detail="Only staff can access reports")

    document = crud_patient.get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Report not found")

    download_url = crud_patient.create_document_download_url(
        storage_path=document.FilePath,
        expires_in_seconds=expires_in_seconds,
    )

    return {
        "DocumentID": document.DocumentID,
        "FileName": document.FileName,
        "FilePath": document.FilePath,
        "DownloadURL": download_url,
        "ExpiresInSeconds": expires_in_seconds,
    }
