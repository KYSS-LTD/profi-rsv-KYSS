from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.employees.repositories import EmployeeRepository
from app.employees.schemas import EmployeeCreate, EmployeeUpdate
from app.models.models import Employee, TelegramAccountLink


class EmployeeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmployeeRepository(db)
        self.audit = AuditService(db)

    def list(self, user):
        return self.repo.list_for_org(user.organization_id)

    def create(self, payload: EmployeeCreate, user):
        employee = Employee(organization_id=user.organization_id, full_name=payload.full_name, email=str(payload.email) if payload.email else None, role=payload.role.value, telegram_id=payload.telegram_id)
        self.repo.save(employee)
        if payload.telegram_id:
            self.db.add(TelegramAccountLink(organization_id=user.organization_id, employee_id=employee.id, telegram_id=payload.telegram_id, is_active=True))
            self.db.commit()
        self.audit.log(action="Create Employee", organization_id=user.organization_id, user_id=user.id, entity_type="Employee", entity_id=employee.id, metadata={"role": employee.role})
        return employee

    def update(self, employee_id: UUID, payload: EmployeeUpdate, user):
        employee = self.repo.get_for_org(employee_id, user.organization_id, user.role)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        old_role = employee.role
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field == "role" and value is not None:
                value = value.value
            if field == "email" and value is not None:
                value = str(value)
            setattr(employee, field, value)
        self.repo.save(employee)
        action = "Change Role" if payload.role and old_role != employee.role else "Update Employee"
        self.audit.log(action=action, organization_id=employee.organization_id, user_id=user.id, entity_type="Employee", entity_id=employee.id, metadata={"old_role": old_role, "new_role": employee.role})
        return employee

    def deactivate(self, employee_id: UUID, user):
        employee = self.repo.get_for_org(employee_id, user.organization_id, user.role)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        employee.is_active = False
        self.repo.save(employee)
        self.audit.log(action="Update Employee", organization_id=employee.organization_id, user_id=user.id, entity_type="Employee", entity_id=employee.id, metadata={"is_active": False})
        return employee

    def delete(self, employee_id: UUID, user):
        employee = self.repo.get_for_org(employee_id, user.organization_id, user.role)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        org_id = employee.organization_id
        self.repo.delete(employee)
        self.audit.log(action="Delete Employee", organization_id=org_id, user_id=user.id, entity_type="Employee", entity_id=employee_id)
        return {"status": "deleted"}
