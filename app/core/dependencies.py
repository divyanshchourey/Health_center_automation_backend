from fastapi import Depends, HTTPException, status  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from app import models
from app.core.security import get_current_user
from app.database import get_db


def require_role(*role_names: str, role_ids: set[int] | None = None):
    normalized_names = {r.strip().lower() for r in role_names if r}
    role_ids = role_ids or set()

    def _dep(current_user: models.User = Depends(get_current_user)) -> models.User:
        role_name = (getattr(getattr(current_user, "role", None), "RoleName", "") or "").strip().lower()
        if current_user.RoleID in role_ids or role_name in normalized_names:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized for this action.",
        )

    return _dep


def verify_lab_access(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("lab", "admin", role_ids={1, 5})),
) -> int:
    # Admins have access to all labs
    if current_user.RoleID == 1:
        return lab_id
        
    lab = db.query(models.LabCenter).filter(models.LabCenter.OwnerUserID == current_user.UserID).first()
    if not lab or lab.LabID != lab_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this Lab Center.",
        )
    return lab_id
