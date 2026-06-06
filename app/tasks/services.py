from __future__ import annotations

from datetime import datetime
import asyncio
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.common.access_scope import AccessScopeService
from app.common.enums import ConfirmationStatus, Permission, TaskStatus
from app.common.security import decrypt_secret
from app.common.rbac import has_permission
from app.common.state_machine import assert_valid_transition
from app.models.models import BoardIntegration, ColumnMapping, Employee, EmployeeBoardMapping, KomandusTask, TaskConfirmation
from app.telegram.service import TelegramDeliveryError, TelegramService
from app.monitoring.metrics import increment
from app.tasks.repositories import V2TaskRepository
from app.tasks.schemas import V2TaskCreate
from app.yougile.provider import YouGileProvider


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
        task = KomandusTask(organization_id=user.organization_id, employee_id=payload.employee_id, department_id=payload.department_id, team_id=payload.team_id, title=payload.title, description=payload.description, due_at=payload.due_at, status=TaskStatus.OPEN.value)
        self.repo.save(task)
        self._send_task_confirmation_if_possible(task)
        self.audit.log(action="Create Task", organization_id=user.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id)
        return task

    def create_from_llm(self, *, organization_id, employee_id, title, description, source_chat_id, source_message_id, confidence, llm_model, extraction_version, department_id=None, team_id=None, organization_chat_id=None, source_excerpt=None):
        if confidence >= 0.80:
            status = TaskStatus.PENDING_CONFIRMATION.value
        else:
            status = TaskStatus.DETECTED.value
        task = KomandusTask(organization_id=organization_id, employee_id=employee_id, department_id=department_id, team_id=team_id, organization_chat_id=organization_chat_id, title=title, description=description, source_chat_id=source_chat_id, source_message_id=source_message_id, llm_confidence=confidence, llm_model=llm_model, extraction_version=extraction_version, status=status, ai_summary=description, source_excerpt=source_excerpt or description)
        self.repo.save(task)
        if confidence >= 0.80:
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
        if new_status == TaskStatus.CANCELLED:
            task.rejected_at = datetime.utcnow()
        self.repo.save(task)
        self.sync_to_yougile(task)
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
            task.status = TaskStatus.OPEN.value
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
        if approved:
            self.sync_to_yougile(task)
            self._notify_manager(task, "accepted")
        else:
            self._notify_rejection(task, reason)
        self.audit.log(action=action, organization_id=task.organization_id, user_id=user.id, entity_type="Task", entity_id=task.id, metadata={"reason": reason})
        return task

    def sync_to_yougile(self, task: KomandusTask) -> None:
        integration = (
            self.db.query(BoardIntegration)
            .filter(
                BoardIntegration.organization_id == task.organization_id,
                BoardIntegration.provider == "yougile",
                BoardIntegration.is_active.is_(True),
            )
            .order_by(BoardIntegration.created_at.desc())
            .first()
        )
        if not integration:
            return
        try:
            token = decrypt_secret(integration.encrypted_api_token)
            provider = YouGileProvider(token)
            column = self._yougile_column_for_status(integration.id, task.status)
            payload = self._yougile_payload(task, column)
            if task.external_task_id:
                result = asyncio.run(provider.update_task(task.external_task_id, payload))
            else:
                result = asyncio.run(provider.create_task(payload))
                task.external_task_id = str(result.get("id") or result.get("taskId") or result.get("_id") or "") or None
                task.external_task_url = result.get("url") or self._yougile_task_url(task.external_task_id)
            self.db.commit()
        except Exception as exc:
            self.audit.log(
                action="YouGile Sync Failed",
                organization_id=task.organization_id,
                entity_type="Task",
                entity_id=task.id,
                metadata={"error": str(exc)},
            )

    def _yougile_column_for_status(self, integration_id, status: str) -> str | None:
        mapping = (
            self.db.query(ColumnMapping)
            .filter(ColumnMapping.board_integration_id == integration_id, ColumnMapping.task_status == status)
            .first()
        )
        if not mapping and status == TaskStatus.OPEN.value:
            mapping = (
                self.db.query(ColumnMapping)
                .filter(ColumnMapping.board_integration_id == integration_id, ColumnMapping.task_status.in_(["TO_DO", "OPEN"]))
                .first()
            )
        return mapping.external_column_id if mapping else None

    def _yougile_payload(self, task: KomandusTask, column_id: str | None) -> dict:
        payload = {"title": task.title}
        if task.description:
            payload["description"] = task.description
        if column_id:
            payload["columnId"] = column_id
        if task.due_at:
            payload["deadline"] = int(task.due_at.timestamp() * 1000)
        if task.employee_id:
            mapping = (
                self.db.query(EmployeeBoardMapping)
                .filter(EmployeeBoardMapping.organization_id == task.organization_id, EmployeeBoardMapping.employee_id == task.employee_id)
                .first()
            )
            if mapping:
                payload["assigned"] = [mapping.external_user_id]
        return payload

    def _yougile_task_url(self, external_task_id: str | None) -> str | None:
        return f"https://ru.yougile.com/task/{external_task_id}" if external_task_id else None

    def _notify_manager(self, task: KomandusTask, action: str, reason: str | None = None) -> None:
        if not task.employee_id:
            return
        employee = self.db.query(Employee).filter(Employee.id == task.employee_id).first()
        if not employee or not employee.manager_id:
            return
        manager = self.db.query(Employee).filter(Employee.id == employee.manager_id).first()
        if not manager or not manager.telegram_id:
            return
        if action == "accepted":
            text = f"✅ {employee.full_name} принял задачу: {task.title}"
        else:
            text = f"❌ {employee.full_name} отклонил задачу: {task.title}\nПричина: {reason or 'не указана'}"
        try:
            asyncio.run(self.telegram.send_manager_notification(manager.telegram_id, text))
        except TelegramDeliveryError:
            return


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
        if employee:
            self._notify_manager(task, "rejected", reason)
        text = f"❌ Задача отклонена: {task.title}\nПричина: {reason or 'не указана'}"
        for chat_id in set(recipients):
            try:
                asyncio.run(self.telegram.send_manager_notification(chat_id, text))
            except TelegramDeliveryError:
                continue
