from __future__ import annotations

from datetime import datetime
import asyncio
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.common.access_scope import AccessScopeService
from app.common.enums import ConfirmationStatus, Permission, TaskStatus
from app.common.rbac import has_permission
from app.common.state_machine import assert_valid_transition
from app.models.models import Employee, KomandusTask, TaskConfirmation
from app.telegram.service import TelegramDeliveryError, TelegramService
from app.monitoring.metrics import increment
from app.tasks.repositories import V2TaskRepository
from app.tasks.schemas import V2TaskCreate


class V2TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = V2TaskRepository(db)
        self.audit = AuditService(db)
        self.telegram = TelegramService()

    def list(self, user):
        return self.repo.list_for_user(user)

    def create_manual(self, payload: V2TaskCreate, user):
        if not has_permission(user.role, Permission.CAN_ASSIGN_TASKS):
            raise HTTPException(status_code=403, detail="Missing permission: can_assign_tasks")
        if payload.employee_id and not AccessScopeService(self.db).can_access_employee(user, payload.employee_id):
            raise HTTPException(status_code=403, detail="Assignee outside access scope")
        task = KomandusTask(organization_id=user.organization_id, employee_id=payload.employee_id, department_id=payload.department_id, team_id=payload.team_id, title=payload.title, description=payload.description, due_at=payload.due_at, status=TaskStatus.TO_DO.value)
        self.repo.save(task)
        self._send_task_confirmation_if_possible(task)
        self.audit.log(action="Create Task", organization_id=user.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id)
        return task

    def create_from_llm(self, *, organization_id, employee_id, title, description, source_chat_id, source_message_id, confidence, llm_model, extraction_version, department_id=None, team_id=None, organization_chat_id=None, source_excerpt=None, notify: bool = True):
        # Product spec: confidence above 85% goes straight to the board; below that
        # the task waits for explicit confirmation.
        status = TaskStatus.ACCEPTED.value if confidence > 0.85 else TaskStatus.PENDING_CONFIRMATION.value
        task = KomandusTask(organization_id=organization_id, employee_id=employee_id, department_id=department_id, team_id=team_id, organization_chat_id=organization_chat_id, title=title, description=description, source_chat_id=source_chat_id, source_message_id=source_message_id, llm_confidence=confidence, llm_model=llm_model, extraction_version=extraction_version, status=status, ai_summary=description, source_excerpt=source_excerpt or description)
        self.repo.save(task)
        if notify and confidence > 0.85:
            self._send_task_confirmation_if_possible(task)
        confirmation = TaskConfirmation(organization_id=organization_id, task_id=task.id, employee_id=employee_id, status=ConfirmationStatus.PENDING.value)
        self.db.add(confirmation); self.db.commit()
        increment("task_detection_total")
        return task

    def _send_task_confirmation_if_possible(self, task: KomandusTask) -> None:
        if not task.employee_id:
            return
        employee = self.db.query(Employee).filter(Employee.id == task.employee_id, Employee.is_active.is_(True)).first()
        if not employee or not employee.telegram_id:
            return
        try:
            asyncio.run(self.telegram.send_task_confirmation(employee, task))
        except TelegramDeliveryError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    def update(self, task_id: UUID, payload, user):
        task = self.repo.get_scoped(task_id, user)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        values = payload.model_dump(exclude_unset=True)
        new_assignee = values.get("employee_id")
        if "employee_id" in values and new_assignee is not None and not AccessScopeService(self.db).can_access_employee(user, new_assignee):
            raise HTTPException(status_code=403, detail="Assignee outside access scope")
        for field, value in values.items():
            setattr(task, field, value)
        self.repo.save(task)
        self.audit.log(action="Update Task", organization_id=task.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id, metadata={"fields": sorted(values.keys())})
        return task

    def change_status(self, task_id: UUID, new_status: TaskStatus, user):
        task = self.repo.get_scoped(task_id, user)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        try:
            assert_valid_transition(task.status, new_status.value)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        old = task.status
        task.status = new_status.value
        if new_status == TaskStatus.DONE:
            task.completed_at = datetime.utcnow()
        self.repo.save(task)
        self.audit.log(action="Change Task Deadline" if old == task.status and task.due_at else "Move Task", organization_id=task.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id, metadata={"old_status": old, "new_status": task.status})
        return task

    def confirm(self, task_id: UUID, approved: bool, reason: str | None, user):
        task = self.repo.get_scoped(task_id, user)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        confirmation = self.db.query(TaskConfirmation).filter(TaskConfirmation.task_id == task.id).first()
        if not confirmation:
            confirmation = TaskConfirmation(organization_id=task.organization_id, task_id=task.id, employee_id=task.employee_id)
            self.db.add(confirmation)
        confirmation.responded_at = datetime.utcnow()
        if approved:
            task.status = TaskStatus.ACCEPTED.value
            task.accepted_at = datetime.utcnow()
            confirmation.status = ConfirmationStatus.APPROVED.value
            increment("task_accept_total")
            action = "Accept Task"
        else:
            if not reason or not reason.strip():
                raise HTTPException(status_code=422, detail="Decline reason is required")
            task.status = TaskStatus.REJECTED.value
            task.rejected_at = datetime.utcnow()
            confirmation.status = ConfirmationStatus.DECLINED.value
            confirmation.decline_reason = reason
            increment("task_reject_total")
            action = "Reject Task"
        self.db.commit(); self.db.refresh(task)
        if not approved:
            self._notify_rejection(task, reason)
        self.audit.log(action=action, organization_id=task.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id, metadata={"reason": reason})
        return task


    def _notify_rejection(self, task: KomandusTask, reason: str | None) -> None:
        if not task.employee_id:
            return
        employee = self.db.query(Employee).filter(Employee.id == task.employee_id).first()
        recipients: list[int] = []
        if employee and employee.manager_id:
            manager = self.db.query(Employee).filter(Employee.id == employee.manager_id).first()
            if manager and manager.telegram_id:
                recipients.append(manager.telegram_id)
        if task.current_owner_user_id:
            owner_employee = self.db.query(Employee).filter(Employee.user_id == task.current_owner_user_id).first()
            if owner_employee and owner_employee.telegram_id:
                recipients.append(owner_employee.telegram_id)
        text = f"❌ Задача отклонена: {task.title}\nПричина: {reason or 'не указана'}"
        for chat_id in set(recipients):
            try:
                asyncio.run(self.telegram.send_manager_notification(chat_id, text))
            except TelegramDeliveryError:
                continue
