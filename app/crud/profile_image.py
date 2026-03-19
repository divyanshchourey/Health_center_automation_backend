from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from app import models
from app.core.supabase_client import SUPABASE_URL, supabase

PROFILE_IMAGE_BUCKET = "profile_image"
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_PROFILE_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


def _build_public_url(storage_path: str) -> str:
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured.")
    return f"{SUPABASE_URL}/storage/v1/object/public/{PROFILE_IMAGE_BUCKET}/{storage_path}"


def _extract_storage_path(file_path_or_url: str | None) -> str | None:
    if not file_path_or_url:
        return None

    if file_path_or_url.startswith(("http://", "https://")):
        parsed = urlparse(file_path_or_url)
        marker = f"/storage/v1/object/public/{PROFILE_IMAGE_BUCKET}/"
        if marker in parsed.path:
            return parsed.path.split(marker, 1)[1]
        return None

    return file_path_or_url


def _get_profile_model(role_type: str):
    normalized_role = role_type.strip().lower()
    if normalized_role == "doctor":
        return models.DoctorProfile, "DoctorID", normalized_role
    if normalized_role == "employee":
        return models.Employee, "EmployeeID", normalized_role
    raise ValueError("Invalid role_type. Use doctor or employee.")


def upsert_profile_image(
    db: Session,
    user_id: int,
    role_type: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str | None,
):
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValueError("Only JPG, JPEG, PNG, WEBP images are allowed.")

    if len(file_bytes) > MAX_PROFILE_IMAGE_SIZE_BYTES:
        raise ValueError("Image size exceeds 5 MB limit.")

    if supabase is None:
        raise RuntimeError("Storage service is not configured.")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    safe_name = Path(file_name).name
    unique_suffix = uuid4().hex[:8]
    final_name = f"{timestamp}_{unique_suffix}_{safe_name}"
    profile_model, id_field_name, normalized_role = _get_profile_model(role_type)
    storage_path = f"{normalized_role}/{user_id}/{final_name}"
    id_field = getattr(profile_model, id_field_name)

    record = (
        db.query(profile_model)
        .filter(id_field == user_id)
        .first()
    )
    if not record:
        # Allow image upload even if profile details were not created yet.
        if normalized_role == "doctor":
            record = models.DoctorProfile(DoctorID=user_id)
        else:
            record = models.Employee(EmployeeID=user_id)
        db.add(record)
        db.flush()

    try:
        supabase.storage.from_(PROFILE_IMAGE_BUCKET).upload(
            storage_path,
            file_bytes,
            {
                "content-type": content_type,
                "upsert": "true",
            },
        )
    except Exception as exc:
        raise RuntimeError(f"Storage upload failed: {str(exc)}") from exc

    old_storage_path = _extract_storage_path(record.FilePath) if record else None
    if record and old_storage_path:
        try:
            supabase.storage.from_(record.StorageBucket).remove([old_storage_path])
        except Exception:
            pass

    record.StorageBucket = PROFILE_IMAGE_BUCKET
    record.FilePath = _build_public_url(storage_path)
    record.FileName = final_name
    record.ContentType = content_type
    if not record.UploadedAt:
        record.UploadedAt = datetime.utcnow()
    record.UpdatedAt = datetime.utcnow()

    try:
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        raise RuntimeError(f"Failed to save profile image metadata: {str(exc)}") from exc

    return record


def get_profile_image_record(db: Session, user_id: int, role_type: str):
    profile_model, id_field_name, _ = _get_profile_model(role_type)
    id_field = getattr(profile_model, id_field_name)
    record = (
        db.query(profile_model)
        .filter(id_field == user_id)
        .first()
    )
    if not record or not record.FilePath:
        return None
    return record


def create_profile_image_download_url(
    storage_path: str,
    storage_bucket: str = PROFILE_IMAGE_BUCKET,
    expires_in_seconds: int = 600,
):
    if storage_path.startswith(("http://", "https://")):
        return storage_path

    if supabase is None:
        raise RuntimeError("Storage service is not configured.")

    try:
        signed = supabase.storage.from_(storage_bucket).create_signed_url(
            storage_path,
            expires_in_seconds,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to create download URL: {str(exc)}") from exc

    if isinstance(signed, dict):
        for key in ("signedURL", "signedUrl", "signed_url"):
            url = signed.get(key)
            if url:
                return url

    url = getattr(signed, "signedURL", None) or getattr(signed, "signed_url", None)
    if url:
        return url

    raise RuntimeError("Failed to create download URL: invalid response from storage.")
