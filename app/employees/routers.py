from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.common.enums import Role
from app.common.rbac import RoleChecker
from app.dependencies import get_db
from app.employees.schemas import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.employees.services import EmployeeService

router = APIRouter(prefix="/api/v2/employees", tags=["Employees"])


@router.get("", response_model=list[EmployeeResponse], summary="List employees", description="List employees in the current organization.")
def list_employees(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return EmployeeService(db).list(current_user)


@router.post("", response_model=EmployeeResponse, status_code=201, summary="Create employee", description="Create an employee and optionally bind Telegram ID. Manager role required.")
def create_employee(payload: EmployeeCreate, current_user=Depends(RoleChecker(Role.MANAGER)), db: Session = Depends(get_db)):
    return EmployeeService(db).create(payload, current_user)


@router.patch("/{employee_id}", response_model=EmployeeResponse, summary="Update employee", description="Update employee profile, role, Telegram ID, or active status. Manager role required.")
def update_employee(employee_id: UUID, payload: EmployeeUpdate, current_user=Depends(RoleChecker(Role.MANAGER)), db: Session = Depends(get_db)):
    return EmployeeService(db).update(employee_id, payload, current_user)


@router.post("/{employee_id}/deactivate", response_model=EmployeeResponse, summary="Deactivate employee", description="Deactivate an employee without deleting historical data. Manager role required.")
def deactivate_employee(employee_id: UUID, current_user=Depends(RoleChecker(Role.MANAGER)), db: Session = Depends(get_db)):
    return EmployeeService(db).deactivate(employee_id, current_user)


@router.post("/{employee_id}/activate", response_model=EmployeeResponse, summary="Activate employee", description="Reactivate an employee and their user account. Manager role required.")
def activate_employee(employee_id: UUID, current_user=Depends(RoleChecker(Role.MANAGER)), db: Session = Depends(get_db)):
    return EmployeeService(db).activate(employee_id, current_user)


@router.post("/{employee_id}/restore", response_model=EmployeeResponse, summary="Restore employee", description="Alias for activation after soft deletion. Manager role required.")
def restore_employee(employee_id: UUID, current_user=Depends(RoleChecker(Role.MANAGER)), db: Session = Depends(get_db)):
    return EmployeeService(db).restore(employee_id, current_user)


@router.delete("/{employee_id}", summary="Soft delete employee", description="Soft-delete an employee by setting is_active=false. Manager role required.")
def delete_employee(employee_id: UUID, current_user=Depends(RoleChecker(Role.MANAGER)), db: Session = Depends(get_db)):
    return EmployeeService(db).delete(employee_id, current_user)
