from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.models import Employee
from app.services.auth_service import decode_token

MANAGEMENT_ROLES = {"OWNER", "ADMIN", "MANAGER"}
ALLOWED_ROLES = MANAGEMENT_ROLES | {"EMPLOYEE", "OBSERVER"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_employee(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Employee:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token is required")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    employee = db.query(Employee).filter(Employee.id == int(payload["sub"]), Employee.is_active.is_(True)).first()
    if employee is None:
        raise HTTPException(status_code=401, detail="Employee not found")
    return employee


def require_manager(current: Employee = Depends(get_current_employee)) -> Employee:
    if current.role not in MANAGEMENT_ROLES:
        raise HTTPException(status_code=403, detail="Manager role is required")
    return current
