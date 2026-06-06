from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.enums import OrganizationMode, Role, TaskSourceType, TaskStatus
from app.models.models import Department, Employee, KomandusTask, Organization, OrganizationChat, TaskSource, Team, TelegramConnectCode


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
        row = TelegramConnectCode(organization_id=user.organization_id, department_id=payload.department_id, team_id=payload.team_id, code=code, expires_at=expires_at)
        self.db.add(row)
        self.db.commit()
        return {"code": code, "command": f"/connect {code}", "expires_at": expires_at, "instruction": ["Добавьте бота в рабочий чат или topic supergroup.", "Назначьте бота администратором.", f"Выполните команду /connect {code} в нужном чате или topic.", "Командус создаст TaskSource и привяжет источник к отделу/команде."]}

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
        if user.role in {Role.OWNER.value, Role.ADMIN.value}:
            return None
        if self.is_simple_mode(user.organization_id) and user.role == Role.MANAGER.value:
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


    def list_task_sources(self, user):
        query = self.db.query(TaskSource).filter(TaskSource.organization_id == user.organization_id)
        allowed_department_ids = self._allowed_department_ids(user)
        if allowed_department_ids is not None:
            query = query.filter(TaskSource.department_id.in_(allowed_department_ids))
        return query.order_by(TaskSource.created_at.desc()).all()

    def ensure_task_source_from_chat(self, *, organization_id, telegram_chat_id: int, title: str, chat_type: str | None = None, telegram_topic_id: int | None = None, department_id=None, team_id=None) -> TaskSource:
        source_type = TaskSourceType.TELEGRAM_TOPIC.value if telegram_topic_id else TaskSourceType.TELEGRAM_CHAT.value
        source = self.db.query(TaskSource).filter(
            TaskSource.organization_id == organization_id,
            TaskSource.source_type == source_type,
            TaskSource.telegram_chat_id == telegram_chat_id,
            TaskSource.telegram_topic_id == telegram_topic_id,
        ).first()
        if source:
            source.title = title or source.title
            source.department_id = department_id or source.department_id
            source.team_id = team_id or source.team_id
            source.is_active = True
            self.db.commit(); self.db.refresh(source)
            return source
        source = TaskSource(organization_id=organization_id, source_type=source_type, telegram_chat_id=telegram_chat_id, telegram_topic_id=telegram_topic_id, title=title, department_id=department_id, team_id=team_id, metadata_json={"chat_type": chat_type})
        self.db.add(source); self.db.commit(); self.db.refresh(source)
        return source

    def get_mode(self, user):
        organization = self.db.query(Organization).filter(Organization.id == user.organization_id).first()
        return {"mode": organization.org_mode if organization else OrganizationMode.SIMPLE.value, "hierarchy_setup_state": organization.hierarchy_setup_state if organization else None}

    def start_hierarchy_wizard(self, user):
        organization = self._organization(user)
        if organization.org_mode == OrganizationMode.HIERARCHY.value:
            return self._wizard_response(organization)
        organization.hierarchy_setup_state = self._default_wizard_state()
        self.db.commit(); self.db.refresh(organization)
        return self._wizard_response(organization)

    def update_hierarchy_wizard(self, payload, user):
        organization = self._organization(user)
        state = {**self._default_wizard_state(), **(organization.hierarchy_setup_state or {})}
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                state[field] = value
        organization.hierarchy_setup_state = state
        self.db.commit(); self.db.refresh(organization)
        return self._wizard_response(organization)

    def confirm_hierarchy_mode(self, user):
        organization = self._organization(user)
        response = self._wizard_response(organization)
        if not response["can_confirm"]:
            raise HTTPException(status_code=409, detail={"message": "Hierarchy wizard is incomplete", "checklist": response["checklist"]})
        organization.org_mode = OrganizationMode.HIERARCHY.value
        self.db.commit(); self.db.refresh(organization)
        return self._wizard_response(organization)

    def is_simple_mode(self, organization_id) -> bool:
        organization = self.db.query(Organization).filter(Organization.id == organization_id).first()
        return not organization or organization.org_mode == OrganizationMode.SIMPLE.value

    def _organization(self, user):
        organization = self.db.query(Organization).filter(Organization.id == user.organization_id).first()
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        return organization

    def _default_wizard_state(self):
        return {"step": 1, "departments_ready": False, "teams_ready": False, "managers_ready": False, "employees_distributed": False, "telegram_sources_ready": False}

    def _wizard_response(self, organization):
        state = {**self._default_wizard_state(), **(organization.hierarchy_setup_state or {})}
        checklist = []
        labels = {
            "departments_ready": "Создать отделы",
            "teams_ready": "Создать команды",
            "managers_ready": "Назначить руководителей",
            "employees_distributed": "Распределить сотрудников",
            "telegram_sources_ready": "Привязать Telegram источники",
        }
        for key, label in labels.items():
            if not state.get(key):
                checklist.append(label)
        return {"mode": organization.org_mode, "hierarchy_setup_state": state, "can_confirm": not checklist, "checklist": checklist}
