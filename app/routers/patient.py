from datetime import date
import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from app import models, schemas
from app.core.security import get_current_user
from app.crud import lab as crud_lab
from app.crud import patient as crud_patient
from app.database import get_db

router = APIRouter(prefix="/patient", tags=["Patient Dashboard"])


@router.get("/", response_model=list[schemas.PatientListResponse])
def list_patients(db: Session = Depends(get_db)):
    """List all patients with basic details"""
    return crud_patient.get_all_patients(db)


@router.get("/doctors", response_model=list[schemas.DoctorListResponse])
def list_doctors_for_patient(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can view doctors")
    return crud_patient.get_all_doctors(db)


@router.get("/labs", response_model=list[schemas.LabCenterResponse])
def list_labs_for_patient(db: Session = Depends(get_db)):
    return crud_lab.list_labs(db)


@router.get("/labs/{lab_id}/tests", response_model=list[schemas.InvestigationResponse])
def list_tests_of_lab(lab_id: int, db: Session = Depends(get_db)):
    try:
        return crud_lab.list_tests_by_lab(db=db, lab_id=lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/labs/{lab_id}/bookings", response_model=schemas.InvestigationBookingResponse)
def create_lab_booking(
    lab_id: int,
    payload: schemas.InvestigationBookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can create booking")

    if payload.LabID != lab_id:
        raise HTTPException(status_code=400, detail="LabID mismatch between path and payload")

    try:
        return crud_lab.create_booking(
            db=db,
            patient_id=current_user.UserID,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/bookings", response_model=list[schemas.InvestigationBookingResponse])
def list_my_lab_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    user_id: int = Query(...),
    date: date | None = Query(default=None),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can view bookings")
    if current_user.UserID != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own appointments")

    try:
        return crud_lab.list_patient_bookings(
            db=db,
            patient_id=user_id,
            query_date=date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    


@router.get("/bookings/{booking_id}/bill", response_model=schemas.LabCenterBillingResponse)
def get_my_lab_bill(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can view bill")
    try:
        return crud_lab.get_patient_bill(
            db=db,
            patient_id=current_user.UserID,
            booking_id=booking_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bookings/{booking_id}/bill/pay", response_model=schemas.LabCenterBillingResponse)
def pay_my_lab_bill(
    booking_id: int,
    payload: schemas.LabCenterBillingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can register payment")
    try:
        return crud_patient.pay_lab_bill(
            db=db,
            patient_id=current_user.UserID,
            booking_id=booking_id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/appointments/{appointment_id}/doctor-bill", response_model=schemas.DoctorBillingResponse)
def get_my_doctor_bill(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can view doctor bill")

    bill = crud_patient.get_patient_doctor_bill(
        db=db,
        patient_id=current_user.UserID,
        appointment_id=appointment_id,
    )
    if not bill:
        raise HTTPException(status_code=404, detail="Doctor bill not found")
    return bill


@router.post("/appointments/{appointment_id}/doctor-bill/pay", response_model=schemas.DoctorBillingResponse)
def pay_my_doctor_bill(
    appointment_id: int,
    payload: schemas.DoctorBillingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can register payment")
    try:
        return crud_patient.pay_doctor_bill(
            db=db,
            patient_id=current_user.UserID,
            appointment_id=appointment_id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/appointments/{appointment_id}/consultation", response_model=schemas.ConsultationResponse)
def get_my_consultation(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can view consultation")
    try:
        consultation = crud_patient.get_patient_consultation_by_appointment(
            db=db,
            patient_id=current_user.UserID,
            appointment_id=appointment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return consultation


@router.get("/prescriptions", response_model=list[schemas.PrescriptionListResponse])
def get_all_my_prescriptions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can access prescriptions")
    try:
        return crud_patient.get_all_patient_prescriptions(
            db=db,
            patient_id=current_user.UserID,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{user_id}", response_model=schemas.PatientProfileResponse)
def get_patient_profile(user_id: int, db: Session = Depends(get_db)):
    profile = crud_patient.get_patient_profile(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found"
        )
    return profile


@router.post("/appointments", response_model=schemas.AppointmentResponse)
def create_appointment(
    data: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can create appointment")
    try:
        return crud_patient.create_appointment_for_patient(
            db=db,
            patient_id=current_user.UserID,
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{user_id}", response_model=schemas.PatientProfileResponse)
def create_or_update_patient_profile(
    user_id: int, data: schemas.PatientProfileCreate, db: Session = Depends(get_db)
):
    profile = crud_patient.create_or_update_patient_profile(db, user_id, data)
    return profile


@router.delete("/{user_id}")
def delete_patient_profile(user_id: int, db: Session = Depends(get_db)):
    success = crud_patient.delete_patient_profile(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found"
        )
    return {"message": "Patient profile deleted successfully"}


@router.get("/documents/me", response_model=list[schemas.AppointmentResponse])
def list_my_records(
    user_id: int = Query(...),
    date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can access appointments")
    if current_user.UserID != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own appointments")

    try:
        return crud_patient.get_patient_appointments(
            db=db,
            patient_id=user_id,
            query_date=date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/appointments/categorized", response_model=schemas.CategorizedAppointmentsResponse)
def list_my_categorized_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can access appointments")

    return crud_patient.get_categorized_appointments(
        db=db,
        patient_id=current_user.UserID,
    )


@router.get("/bookings/{booking_id}/reports", response_model=list[schemas.ReportResponse])
def list_my_reports_for_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can access reports")

    try:
        return crud_patient.get_patient_documents(
            db=db,
            patient_id=current_user.UserID,
            booking_id=booking_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reports/{document_id}/download")
def get_my_document_download_link(
    document_id: int,
    expires_in_seconds: int = Query(default=600, ge=60, le=86400),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.RoleID != 3:
        raise HTTPException(status_code=403, detail="Only patient can access reports")

    document = crud_patient.get_patient_document(
        db=db, patient_id=current_user.UserID, document_id=document_id
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        download_url = crud_patient.create_document_download_url(
            storage_path=document.FilePath,
            expires_in_seconds=expires_in_seconds,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "DocumentID": document.DocumentID,
        "FileName": document.FileName,
        "FilePath": document.FilePath,
        "DownloadURL": download_url,
        "ExpiresInSeconds": expires_in_seconds,
    }



