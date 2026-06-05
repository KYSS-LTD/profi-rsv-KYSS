from uuid import UUID
import secrets
import string
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.common.security import hash_password
from app.employees.repositories import EmployeeRepository
from app.employees.schemas import EmployeeCreate, EmployeeUpdate
from app.models.models import Employee, TelegramAccountLink, User, Department, Team


class EmployeeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmployeeRepository(db)
        self.audit = AuditService(db)

    def list(self, user):
        return self.repo.list_for_org(user.organization_id)

    def create(self, payload: EmployeeCreate, user):
        self._validate_department_team(user.organization_id, payload.department_id, payload.team_id)
        password = self._generate_password()
        email = str(payload.email).lower() if payload.email else None
        db_user = None
        if email:
            db_user = self.db.query(User).filter(User.email == email).first()
            if db_user:
                raise HTTPException(status_code=409, detail="User with this email already exists")
            db_user = User(
                organization_id=user.organization_id,
                email=email,
                password_hash=hash_password(password),
                full_name=payload.full_name,
                role=payload.role.value,
                department_id=payload.department_id,
                team_id=payload.team_id,
                must_change_password=True,
                is_active=True,
            )
            self.db.add(db_user)
            self.db.flush()
        employee = Employee(
            organization_id=user.organization_id,
            user_id=db_user.id if db_user else None,
            full_name=payload.full_name,
            email=email,
            role=payload.role.value,
            department_id=payload.department_id,
            team_id=payload.team_id,
            position=payload.position,
            telegram_username=self._normalize_username(payload.telegram_username),
            telegram_status="PENDING",
            generated_password=password if email else None,
        )
        self.repo.save(employee)
        self.audit.log(action="Create Employee", organization_id=user.organization_id, user_id=user.id, entity_type="Employee", entity_id=employee.id, metadata={"role": employee.role, "department_id": str(employee.department_id) if employee.department_id else None})
        return employee

    def update(self, employee_id: UUID, payload: EmployeeUpdate, user):
        employee = self.repo.get_for_org(employee_id, user.organization_id, user.role)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        values = payload.model_dump(exclude_unset=True)
        self._validate_department_team(user.organization_id, values.get("department_id", employee.department_id), values.get("team_id", employee.team_id))
        old_role = employee.role
        for field, value in values.items():
            if field == "role" and value is not None:
                value = value.value
            if field == "email" and value is not None:
                value = str(value).lower()
            if field == "telegram_username" and value is not None:
                value = self._normalize_username(value)
            setattr(employee, field, value)
        if employee.user_id:
            db_user = self.db.query(User).filter(User.id == employee.user_id).first()
            if db_user:
                db_user.full_name = employee.full_name
                db_user.role = employee.role
                db_user.department_id = employee.department_id
                db_user.team_id = employee.team_id
                if employee.email:
                    db_user.email = employee.email
        self.repo.save(employee)
        action = "Change Role" if payload.role and old_role != employee.role else "Update Employee"
        self.audit.log(action=action, organization_id=employee.organization_id, user_id=user.id, entity_type="Employee", entity_id=employee.id, metadata={"old_role": old_role, "new_role": employee.role})
        return employee

    def deactivate(self, employee_id: UUID, user):
        employee = self.repo.get_for_org(employee_id, user.organization_id, user.role)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        employee.is_active = False
        if employee.user_id:
            db_user = self.db.query(User).filter(User.id == employee.user_id).first()
            if db_user:
                db_user.is_active = False
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

    def _validate_department_team(self, organization_id, department_id, team_id):
        if department_id and not self.db.query(Department).filter(Department.id == department_id, Department.organization_id == organization_id).first():
            raise HTTPException(status_code=404, detail="Department not found")
        if team_id:
            team = self.db.query(Team).filter(Team.id == team_id, Team.organization_id == organization_id).first()
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            if department_id and team.department_id != department_id:
                raise HTTPException(status_code=409, detail="Team does not belong to department")

    def _normalize_username(self, username: str | None):
        if not username:
            return None
        username = username.strip()
        return username if username.startswith("@") else f"@{username}"

    def _generate_password(self):
        alphabet = string.ascii_letters + string.digits
        return "Kmd-" + "".join(secrets.choice(alphabet) for _ in range(10))
