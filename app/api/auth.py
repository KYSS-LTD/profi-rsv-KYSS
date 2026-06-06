from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.models import Employee
from app.services.auth_service import create_token, decode_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="email is required")

    employee = db.query(Employee).filter(Employee.email == email, Employee.is_active.is_(True)).first()
    if employee is None:
        raise HTTPException(status_code=401, detail="Employee not found")

    return _token_pair(employee)


@router.post("/refresh")
async def refresh(payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=422, detail="refresh_token is required")
    try:
        decoded = decode_token(refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    employee = db.query(Employee).filter(Employee.id == int(decoded["sub"]), Employee.is_active.is_(True)).first()
    if employee is None:
        raise HTTPException(status_code=401, detail="Employee not found")
    return _token_pair(employee)


def _token_pair(employee: Employee) -> dict:
    return {
        "access_token": create_token(str(employee.id), employee.organization_id, employee.role, "access"),
        "refresh_token": create_token(str(employee.id), employee.organization_id, employee.role, "refresh"),
        "token_type": "bearer",
        "employee": {
            "id": employee.id,
            "organization_id": employee.organization_id,
            "full_name": employee.full_name,
            "email": employee.email,
            "role": employee.role,
        },
    }
