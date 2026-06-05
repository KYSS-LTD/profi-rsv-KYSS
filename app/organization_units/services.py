from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.enums import Role, TaskStatus
from app.models.models import Department, Employee, KomandusTask, OrganizationChat, Team, TelegramConnectCode


class OrganizationUnitService:
    def __init__(self, db: Session):
        self.db = db

    def list_departments(self, user):
        departments = self._department_query(user).order_by(Department.name.asc()).all()
        return [self._department_card(department) for department in departments]

    def create_department(self, payload, user):
        department = Department(organization_id=user.organization_id, name=payload.name.strip(), description=payload.description)
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return self._department_card(department)

    def update_department(self, department_id: UUID, payload, user):
        department = self._get_department(department_id, user)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(department, field, value.strip() if field == "name" and value else value)
        self.db.commit()
        self.db.refresh(department)
        return self._department_card(department)

    def list_teams(self, user, department_id: UUID | None = None):
        query = self.db.query(Team).filter(Team.organization_id == user.organization_id)
        allowed_department_ids = self._allowed_department_ids(user)
        if allowed_department_ids is not None:
            query = query.filter(Team.department_id.in_(allowed_department_ids))
        if department_id:
            query = query.filter(Team.department_id == department_id)
        return query.order_by(Team.name.asc()).all()

    def create_team(self, payload, user):
        department = self._get_department(payload.department_id, user)
        team = Team(organization_id=user.organization_id, department_id=department.id, name=payload.name.strip(), description=payload.description)
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def list_chats(self, user):
        query = self.db.query(OrganizationChat).filter(OrganizationChat.organization_id == user.organization_id)
        allowed_department_ids = self._allowed_department_ids(user)
        if allowed_department_ids is not None:
            query = query.filter(OrganizationChat.department_id.in_(allowed_department_ids))
        return query.order_by(OrganizationChat.connected_at.desc()).all()

    def create_connect_code(self, payload, user):
        if payload.department_id:
            self._get_department(payload.department_id, user)
        code = self._generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        row = TelegramConnectCode(organization_id=user.organization_id, department_id=payload.department_id, code=code, expires_at=expires_at)
        self.db.add(row)
        self.db.commit()
        return {"code": code, "command": f"/connect {code}", "expires_at": expires_at, "instruction": ["Добавьте бота в рабочий чат.", "Назначьте бота администратором.", f"Выполните команду /connect {code} в этом чате."]}

    def set_chat_ai(self, chat_id: UUID, ai_enabled: bool, department_id: UUID | None, user):
        chat = self.db.query(OrganizationChat).filter(OrganizationChat.id == chat_id, OrganizationChat.organization_id == user.organization_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        if department_id:
            self._get_department(department_id, user)
            chat.department_id = department_id
        chat.ai_enabled = ai_enabled
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def _department_query(self, user):
        query = self.db.query(Department).filter(Department.organization_id == user.organization_id)
        allowed_department_ids = self._allowed_department_ids(user)
        if allowed_department_ids is not None:
            query = query.filter(Department.id.in_(allowed_department_ids))
        return query

    def _allowed_department_ids(self, user):
        if user.role in {Role.MANAGER.value, Role.SUPER_ADMIN.value}:
            return None
        if user.department_id:
            return [user.department_id]
        return []

    def _get_department(self, department_id: UUID, user):
        department = self._department_query(user).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        return department

    def _department_card(self, department: Department):
        task_query = self.db.query(KomandusTask).filter(KomandusTask.department_id == department.id)
        task_count = task_query.count()
        overdue = task_query.filter(KomandusTask.status == TaskStatus.OVERDUE.value).count()
        done = task_query.filter(KomandusTask.status == TaskStatus.DONE.value).count()
        employee_count = self.db.query(Employee).filter(Employee.department_id == department.id, Employee.is_active.is_(True)).count()
        efficiency = round((done / task_count) * 100, 1) if task_count else 0
        department.employee_count = employee_count
        department.task_count = task_count
        department.overdue_count = overdue
        department.efficiency = efficiency
        return department

    def _generate_code(self):
        while True:
            suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            code = f"KMD-{suffix}"
            if not self.db.query(TelegramConnectCode).filter(TelegramConnectCode.code == code).first():
                return code
