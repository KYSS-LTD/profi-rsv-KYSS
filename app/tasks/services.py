from __future__ import annotations

from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.common.enums import ConfirmationStatus, TaskStatus
from app.common.state_machine import assert_valid_transition
from app.models.models import KomandusTask, TaskConfirmation
from app.monitoring.metrics import increment
from app.tasks.repositories import V2TaskRepository
from app.tasks.schemas import V2TaskCreate


class V2TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = V2TaskRepository(db)
        self.audit = AuditService(db)

    def list(self, user):
        return self.repo.list_for_org(user.organization_id)

    def create_manual(self, payload: V2TaskCreate, user):
        task = KomandusTask(organization_id=user.organization_id, employee_id=payload.employee_id, title=payload.title, description=payload.description, due_at=payload.due_at, status=TaskStatus.TO_DO.value)
        self.repo.save(task)
        self.audit.log(action="Create Task", organization_id=user.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id)
        return task

    def create_from_llm(self, *, organization_id, employee_id, title, description, source_chat_id, source_message_id, confidence, llm_model, extraction_version):
        status = TaskStatus.ACCEPTED.value if confidence >= 0.85 else TaskStatus.PENDING_CONFIRMATION.value
        task = KomandusTask(organization_id=organization_id, employee_id=employee_id, title=title, description=description, source_chat_id=source_chat_id, source_message_id=source_message_id, llm_confidence=confidence, llm_model=llm_model, extraction_version=extraction_version, status=status)
        self.repo.save(task)
        confirmation = TaskConfirmation(organization_id=organization_id, task_id=task.id, employee_id=employee_id, status=ConfirmationStatus.PENDING.value)
        self.db.add(confirmation); self.db.commit()
        increment("task_detection_total")
        return task

    def change_status(self, task_id: UUID, new_status: TaskStatus, user):
        task = self.repo.get_scoped(task_id, user.organization_id, user.role)
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
        self.audit.log(action="Move Task", organization_id=task.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id, metadata={"old_status": old, "new_status": task.status})
        return task

    def confirm(self, task_id: UUID, approved: bool, reason: str | None, user):
        task = self.repo.get_scoped(task_id, user.organization_id, user.role)
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
            task.status = TaskStatus.REJECTED.value
            task.rejected_at = datetime.utcnow()
            confirmation.status = ConfirmationStatus.DECLINED.value
            confirmation.decline_reason = reason
            increment("task_reject_total")
            action = "Reject Task"
        self.db.commit(); self.db.refresh(task)
        self.audit.log(action=action, organization_id=task.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id, metadata={"reason": reason})
        return task
