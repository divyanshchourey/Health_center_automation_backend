from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from app import schemas
from app.core.dependencies import require_role
from app.crud import lab as crud_lab
from app.database import get_db

router = APIRouter(prefix="/lab", tags=["Lab"])



@router.post("/investigations", response_model=schemas.InvestigationResponse)
def add_investigation(
    payload: schemas.InvestigationCreate,
    db: Session = Depends(get_db),
    _lab_user=Depends(require_role("lab", "admin", role_ids={1, 5})),
):
    try:
        return crud_lab.create_investigation(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/investigations", response_model=list[schemas.InvestigationResponse])
def view_all_tests(
    lab_id: int = Query(...),
    db: Session = Depends(get_db),
    _lab_user=Depends(require_role("lab", "admin", role_ids={1, 5})),
):
    try:
        return crud_lab.list_own_lab_tests(db=db, lab_id=lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/{lab_id}/bookings", response_model=list[schemas.InvestigationBookingResponse])
def list_lab_bookings(
    lab_id: int,
    status: str | None = Query(default=None),
    date: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _lab_user=Depends(require_role("lab", "admin", role_ids={1, 5})),
):
    try:
        return crud_lab.list_lab_bookings(
            db=db,
            lab_id=lab_id,
            status=status,
            date=date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{lab_id}/bookings/{booking_id}/approve", response_model=schemas.InvestigationBookingResponse)
def approve_or_reject_booking(
    lab_id: int,
    booking_id: int,
    payload: schemas.InvestigationBookingCreate,
    db: Session = Depends(get_db),
    _lab_user=Depends(require_role("lab", "admin", role_ids={1, 5})),
):
    try:
        return crud_lab.approve_booking(
            db=db,
            lab_id=lab_id,
            booking_id=booking_id,
            action=payload.action,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{lab_id}/bookings/{booking_id}/bill", response_model=schemas.LabCenterBillingResponse)
def generate_lab_bill(
    lab_id: int,
    booking_id: int,
    payload: schemas.LabCenterBillingCreate,
    db: Session = Depends(get_db),
    _lab_user=Depends(require_role("lab", "admin", role_ids={1, 5})),
):
    try:
        return crud_lab.generate_bill(
            db=db,
            lab_id=lab_id,
            booking_id=booking_id,
            amount=payload.Amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{lab_id}/bookings/{booking_id}/bill", response_model=schemas.LabCenterBillingResponse)
def get_lab_bill_by_booking(
    lab_id: int,
    booking_id: int,
    db: Session = Depends(get_db),
    _lab_user=Depends(require_role("lab", "admin", role_ids={1, 5})),
):
    try:
        return crud_lab.get_lab_bill_by_booking(
            db=db,
            lab_id=lab_id,
            booking_id=booking_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{lab_id}/bookings/{booking_id}/bill/pay", response_model=schemas.PaymentResponse)
def pay_lab_bill_by_lab(
    lab_id: int,
    booking_id: int,
    payload: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    _lab_user=Depends(require_role("lab", "admin", role_ids={1, 5})),
):
    try:
        return crud_lab.record_lab_bill_payment(
            db=db,
            lab_id=lab_id,
            booking_id=booking_id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{lab_id}/bookings/{booking_id}/reports")
async def upload_lab_booking_report(
    lab_id: int,
    booking_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _lab_user=Depends(require_role("lab", "admin", role_ids={1, 5})),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF size exceeds 5 MB limit")

    try:
        saved = crud_lab.upload_booking_report(
            db=db,
            lab_id=lab_id,
            booking_id=booking_id,
            file_name=file.filename or "report.pdf",
            pdf_bytes=file_bytes,
            content_type=file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": "Report uploaded successfully",
        "document_id": saved["document_id"],
        "booking_id": saved["booking_id"],
        "path": saved["path"],
    }
