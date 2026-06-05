from uuid import UUID
import asyncio
import secrets
import string
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.auth.magic import MagicLoginService
from app.core.config import settings
from app.common.access_scope import AccessScopeService
from app.common.security import hash_password
from app.employees.repositories import EmployeeRepository
from app.employees.schemas import EmployeeCreate, EmployeeUpdate
from app.models.models import Employee, TelegramAccountLink, User, Department, Team
from app.telegram.service import TelegramDeliveryError, TelegramService


class EmployeeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmployeeRepository(db)
        self.audit = AuditService(db)
        self.telegram = TelegramService()

    def list(self, user):
        employees = AccessScopeService(self.db).get_visible_employees(user).order_by(Employee.created_at.desc()).all()
        return [self._serialize_employee(employee) for employee in employees]

    def create(self, payload: EmployeeCreate, user):
        self._validate_department_team(user.organization_id, payload.department_id, payload.team_id)
        self._validate_manager(user.organization_id, payload.manager_id)
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
        normalized_username = self._normalize_username(payload.telegram_username)
        known_link = self.db.query(TelegramAccountLink).filter(TelegramAccountLink.organization_id == user.organization_id, TelegramAccountLink.telegram_username == normalized_username, TelegramAccountLink.is_active.is_(True)).first() if normalized_username else None
        employee = Employee(
            organization_id=user.organization_id,
            user_id=db_user.id if db_user else None,
            full_name=payload.full_name,
            manager_id=payload.manager_id,
            email=email,
            role=payload.role.value,
            department_id=payload.department_id,
            team_id=payload.team_id,
            position=payload.position,
            telegram_username=normalized_username,
            telegram_status="CONNECTED" if known_link else "PENDING",
            telegram_id=known_link.telegram_id if known_link else None,
            generated_password=None,
        )
        self.repo.save(employee)
        if known_link:
            known_link.employee_id = employee.id
            self.db.commit()
            self._send_magic_login(employee)
        self.audit.log(action="Create Employee", organization_id=user.organization_id, user_id=user.id, entity_type="Employee", entity_id=employee.id, metadata={"role": employee.role, "department_id": str(employee.department_id) if employee.department_id else None})
        return self._serialize_employee(employee)

    def update(self, employee_id: UUID, payload: EmployeeUpdate, user):
        employee = self.repo.get_for_org(employee_id, user.organization_id, user.role)
        if employee and not AccessScopeService(self.db).can_access_employee(user, employee.id):
            raise HTTPException(status_code=403, detail="Employee outside access scope")
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        values = payload.model_dump(exclude_unset=True)
        self._validate_department_team(user.organization_id, values.get("department_id", employee.department_id), values.get("team_id", employee.team_id))
        if "manager_id" in values:
            self._validate_manager(user.organization_id, values.get("manager_id"))
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
        return self._serialize_employee(employee)

    def deactivate(self, employee_id: UUID, user):
        return self._set_active(employee_id, user, False, "Deactivate Employee")

    def activate(self, employee_id: UUID, user):
        return self._set_active(employee_id, user, True, "Activate Employee")

    def restore(self, employee_id: UUID, user):
        return self._set_active(employee_id, user, True, "Restore Employee")

    def delete(self, employee_id: UUID, user):
        self._set_active(employee_id, user, False, "Soft Delete Employee")
        return {"status": "deactivated", "id": str(employee_id)}

    def _set_active(self, employee_id: UUID, user, active: bool, action: str):
        employee = self.repo.get_for_org(employee_id, user.organization_id, user.role)
        if employee and not AccessScopeService(self.db).can_access_employee(user, employee.id):
            raise HTTPException(status_code=403, detail="Employee outside access scope")
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        if not AccessScopeService(self.db).can_access_employee(user, employee.id):
            raise HTTPException(status_code=403, detail="Employee outside access scope")
        employee.active = active
        employee.is_active = active
        employee.deactivated_at = None if active else __import__("datetime").datetime.utcnow()
        employee.deactivated_by = None if active else user.id
        if employee.user_id:
            db_user = self.db.query(User).filter(User.id == employee.user_id).first()
            if db_user:
                db_user.is_active = active
        self.repo.save(employee)
        self.audit.log(action=action, organization_id=employee.organization_id, user_id=user.id, entity_type="Employee", entity_id=employee.id, metadata={"is_active": active})
        return self._serialize_employee(employee)

    def _send_login_credentials(self, employee: Employee) -> None:
        self._send_magic_login(employee)

    def _send_magic_login(self, employee: Employee) -> None:
        if not employee.user_id:
            return
        token = MagicLoginService(self.db).create_token(employee.user_id)
        magic_url = MagicLoginService(self.db).build_magic_login_url(token.token)
        try:
            asyncio.run(self.telegram.send_magic_login(employee, magic_url))
        except TelegramDeliveryError as exc:
            self.audit.log(action="Telegram Delivery Failed", organization_id=employee.organization_id, entity_type="Employee", entity_id=employee.id, metadata={"error": str(exc), "flow": "magic_login"})
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    def _serialize_employee(self, employee: Employee) -> dict:
        return {
            "id": employee.id,
            "organization_id": employee.organization_id,
            "user_id": employee.user_id,
            "manager_id": employee.manager_id,
            "full_name": employee.full_name,
            "email": employee.email,
            "role": employee.role,
            "department_id": employee.department_id,
            "team_id": employee.team_id,
            "position": employee.position,
            "telegram_username": employee.telegram_username,
            "telegram_first_name": employee.telegram_first_name,
            "telegram_last_name": employee.telegram_last_name,
            "avatar_url": employee.avatar_url,
            "telegram_status": employee.telegram_status,
            "telegram_connected_at": employee.telegram_connected_at,
            "telegram_id": employee.telegram_id,
            "active": employee.active,
            "deactivated_at": employee.deactivated_at,
            "deactivated_by": employee.deactivated_by,
            "generated_password": None,
            "invitation_text": self._build_invitation_text(),
            "is_active": employee.is_active,
        }

    def _build_invitation_text(self) -> str:
        bot_url = settings.telegram_bot_url or "ссылку на Telegram-бота уточните у администратора"
        return f"Откройте бота Командус: {bot_url}\n1. Откройте бота.\n2. Выполните /start.\n3. Получите ссылку для входа."

    def _validate_manager(self, organization_id, manager_id):
        if manager_id and not self.db.query(Employee).filter(Employee.id == manager_id, Employee.organization_id == organization_id, Employee.is_active.is_(True)).first():
            raise HTTPException(status_code=404, detail="Manager not found")

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
