from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import ALLOWED_ROLES, get_current_employee, get_db, require_manager
from app.models.models import Employee, Organization

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("")
async def list_employees(
    current: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    query = db.query(Employee).filter(Employee.organization_id == current.organization_id)
    if current.role == "EMPLOYEE":
        query = query.filter(Employee.id == current.id)
    return [serialize_employee(employee) for employee in query.order_by(Employee.full_name).all()]


@router.post("", status_code=201)
async def create_employee(
    payload: dict = Body(default_factory=dict),
    current: Employee = Depends(require_manager),
    db: Session = Depends(get_db),
):
    role = (payload.get("role") or "EMPLOYEE").upper()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=422, detail="Unsupported MVP role")

    email = (payload.get("email") or "").strip().lower()
    full_name = (payload.get("full_name") or "").strip()
    if not email or not full_name:
        raise HTTPException(status_code=422, detail="full_name and email are required")
    if db.query(Employee).filter(Employee.email == email).first():
        raise HTTPException(status_code=409, detail="Employee email already exists")

    employee = Employee(
        organization_id=current.organization_id,
        full_name=full_name,
        email=email,
        role=role,
        manager_id=payload.get("manager_id") or current.id,
        telegram_username=normalize_username(payload.get("telegram_username")),
        is_active=bool(payload.get("is_active", True)),
        telegram_connected=False,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return serialize_employee(employee)


@router.patch("/{employee_id}")
async def update_employee(
    employee_id: int,
    payload: dict = Body(default_factory=dict),
    current: Employee = Depends(require_manager),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(Employee.id == employee_id, Employee.organization_id == current.organization_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field in ("full_name", "email", "role", "manager_id", "is_active"):
        if field in payload:
            value = payload[field]
            if field == "role":
                value = str(value).upper()
                if value not in ALLOWED_ROLES:
                    raise HTTPException(status_code=422, detail="Unsupported MVP role")
            if field == "email":
                value = str(value).strip().lower()
            setattr(employee, field, value)
    if "telegram_username" in payload:
        employee.telegram_username = normalize_username(payload.get("telegram_username"))
        if not employee.telegram_username:
            employee.telegram_user_id = None
            employee.telegram_connected = False

    db.commit()
    db.refresh(employee)
    return serialize_employee(employee)


@router.post("/bootstrap-owner", status_code=201)
async def bootstrap_owner(payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    """Create the first organization/OWNER for local MVP setup only."""
    if db.query(Employee).first():
        raise HTTPException(status_code=409, detail="Bootstrap is available only before employees exist")
    organization = Organization(name=payload.get("organization_name") or "Komandus")
    db.add(organization)
    db.flush()
    owner = Employee(
        organization_id=organization.id,
        full_name=payload.get("full_name") or "Owner",
        email=(payload.get("email") or "owner@example.com").lower(),
        role="OWNER",
        telegram_username=normalize_username(payload.get("telegram_username")),
        is_active=True,
        telegram_connected=False,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return serialize_employee(owner)


def normalize_username(username: str | None) -> str | None:
    if not username:
        return None
    normalized = username.strip()
    return normalized[1:] if normalized.startswith("@") else normalized


def serialize_employee(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "organization_id": employee.organization_id,
        "full_name": employee.full_name,
        "email": employee.email,
        "role": employee.role,
        "manager_id": employee.manager_id,
        "telegram_username": f"@{employee.telegram_username}" if employee.telegram_username else None,
        "telegram_user_id": employee.telegram_user_id,
        "is_active": employee.is_active,
        "telegram_connected": employee.telegram_connected,
        "created_at": employee.created_at.isoformat() if employee.created_at else None,
        "updated_at": employee.updated_at.isoformat() if employee.updated_at else None,
    }
