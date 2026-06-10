from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.common.enums import TaskStatus
from app.dependencies import get_db
from app.models.models import Employee, KomandusTask, Organization, ProfileNote, TelegramAccountLink

router = APIRouter(tags=["Profile"])

DONE_STATUSES = {TaskStatus.DONE.value}
CLOSED_STATUSES = {TaskStatus.DONE.value, TaskStatus.REJECTED.value}
OLD_STATUS_BY_V2 = {
    TaskStatus.DETECTED.value: "backlog",
    TaskStatus.PENDING_CONFIRMATION.value: "backlog",
    TaskStatus.ACCEPTED.value: "todo",
    TaskStatus.REJECTED.value: "cancelled",
    TaskStatus.TO_DO.value: "todo",
    TaskStatus.IN_PROGRESS.value: "in_progress",
    TaskStatus.REVIEW.value: "review",
    TaskStatus.DONE.value: "done",
    TaskStatus.OVERDUE.value: "todo",
}


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _find_employee(db: Session, user) -> Employee | None:
    query = db.query(Employee).filter(Employee.organization_id == user.organization_id, Employee.is_active.is_(True))
    employee = query.filter(Employee.user_id == user.id).first()
    if employee:
        return employee
    return query.filter(Employee.email == user.email).first()


def _serialize_task(task: KomandusTask, employee: Employee | None = None) -> dict:
    return {
        "id": str(task.id),
        "team_id": str(task.organization_id),
        "candidate_id": None,
        "external_kanban_id": task.external_task_id,
        "external_kanban_url": task.external_task_url,
        "title": task.title,
        "description": task.description,
        "assignee": employee.full_name if employee else None,
        "assignee_id": str(task.employee_id) if task.employee_id else None,
        "deadline": task.due_at.isoformat() if task.due_at else None,
        "status": OLD_STATUS_BY_V2.get(task.status, "todo"),
        "priority": "medium",
        "source": "telegram_text" if task.source_message_id or task.source_chat_id else "meeting_audio" if task.llm_model else "telegram_text",
        "confidence": task.llm_confidence,
        "created_by_ai": bool(task.llm_model or task.llm_confidence is not None),
        "kanban_provider": "external" if task.external_task_id else "internal",
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "closed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


def _serialize_note(note: ProfileNote) -> dict:
    return {
        "id": str(note.id),
        "user_id": str(note.user_id),
        "team_id": str(note.organization_id),
        "task_id": note.task_id,
        "meeting_id": note.meeting_id,
        "title": note.title,
        "content": note.content,
        "source": note.source,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }


def _user_tasks_query(db: Session, user, employee: Employee | None):
    query = db.query(KomandusTask).filter(KomandusTask.organization_id == user.organization_id)
    if employee:
        return query.filter(KomandusTask.employee_id == employee.id)
    return query.filter(KomandusTask.employee_id.is_(None))


@router.get("/profile/me")
async def get_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    employee = _find_employee(db, current_user)
    telegram_link = None
    if employee:
        telegram_link = db.query(TelegramAccountLink).filter(TelegramAccountLink.employee_id == employee.id, TelegramAccountLink.is_active.is_(True)).first()

    done_count = _user_tasks_query(db, current_user, employee).filter(KomandusTask.status.in_(DONE_STATUSES)).count()
    active_count = _user_tasks_query(db, current_user, employee).filter(~KomandusTask.status.in_(CLOSED_STATUSES)).count()
    xp = done_count * 100 + active_count * 15

    skills = [current_user.role]
    if done_count:
        skills.append("Исполнение задач")
    if active_count:
        skills.append("Управление потоком")

    return {
        "id": str(current_user.id),
        "name": current_user.full_name or current_user.email,
        "telegram_username": f"@{telegram_link.telegram_username}" if telegram_link and telegram_link.telegram_username else None,
        "role": current_user.role,
        "team": organization.name if organization else None,
        "timezone": "UTC",
        "notification_preferences": [],
        "xp": xp,
        "level": "Лидер" if xp >= 1000 else "Опытный" if xp >= 300 else "Участник",
        "skills": skills,
    }


@router.get("/profile/me/tasks")
async def get_profile_tasks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    employee = _find_employee(db, current_user)
    tasks = _user_tasks_query(db, current_user, employee).order_by(KomandusTask.created_at.desc()).all()
    return [_serialize_task(task, employee) for task in tasks]


@router.get("/users/{user_id}/digest")
async def get_user_digest(user_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Digest is available only for the current user")

    employee = _find_employee(db, current_user)
    now = _utc_now_naive()
    user_tasks = _user_tasks_query(db, current_user, employee).order_by(KomandusTask.created_at.desc()).all()
    tasks_today = [task for task in user_tasks if task.created_at and task.created_at.date() == now.date()]
    overdue_tasks = [task for task in user_tasks if task.due_at and task.due_at < now and task.status not in CLOSED_STATUSES]
    upcoming_deadlines = [
        task
        for task in user_tasks
        if task.due_at and task.due_at >= now and task.status not in CLOSED_STATUSES
    ][:5]

    return {
        "user_id": str(current_user.id),
        "date": now.date().isoformat(),
        "tasks_today": [_serialize_task(task, employee) for task in tasks_today],
        "overdue_tasks": [_serialize_task(task, employee) for task in overdue_tasks],
        "upcoming_deadlines": [_serialize_task(task, employee) for task in upcoming_deadlines],
    }


@router.get("/notes/my")
async def get_notes(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    notes = db.query(ProfileNote).filter(ProfileNote.user_id == current_user.id, ProfileNote.organization_id == current_user.organization_id).order_by(ProfileNote.created_at.desc()).all()
    return [_serialize_note(note) for note in notes]


@router.post("/notes", status_code=201)
async def create_note(payload: dict = Body(default_factory=dict), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    title = str(payload.get("title") or "").strip()
    content = str(payload.get("content") or "").strip()
    source = payload.get("source") or "manual"
    if not title or not content:
        raise HTTPException(status_code=422, detail="title and content are required")
    if source not in {"manual", "meeting", "ai_summary"}:
        raise HTTPException(status_code=422, detail="Invalid note source")

    note = ProfileNote(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=title,
        content=content,
        source=source,
        task_id=payload.get("task_id"),
        meeting_id=payload.get("meeting_id"),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return _serialize_note(note)


@router.patch("/notes/{note_id}")
async def update_note(note_id: UUID, payload: dict = Body(default_factory=dict), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(ProfileNote).filter(ProfileNote.id == note_id, ProfileNote.user_id == current_user.id, ProfileNote.organization_id == current_user.organization_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if "title" in payload:
        title = str(payload.get("title") or "").strip()
        if not title:
            raise HTTPException(status_code=422, detail="title is required")
        note.title = title
    if "content" in payload:
        content = str(payload.get("content") or "").strip()
        if not content:
            raise HTTPException(status_code=422, detail="content is required")
        note.content = content
    db.commit()
    db.refresh(note)
    return _serialize_note(note)


@router.delete("/notes/{note_id}")
async def delete_note(note_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(ProfileNote).filter(ProfileNote.id == note_id, ProfileNote.user_id == current_user.id, ProfileNote.organization_id == current_user.organization_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"status": "deleted", "note_id": str(note_id)}


@router.get("/users/{user_id}/achievements")
async def get_achievements(user_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Achievements are available only for the current user")

    employee = _find_employee(db, current_user)
    tasks_query = _user_tasks_query(db, current_user, employee)
    done_task = tasks_query.filter(KomandusTask.status.in_(DONE_STATUSES)).order_by(KomandusTask.completed_at.asc().nullslast()).first()
    done_count = tasks_query.filter(KomandusTask.status.in_(DONE_STATUSES)).count()
    ai_task = tasks_query.filter(or_(KomandusTask.llm_confidence.is_not(None), KomandusTask.llm_model.is_not(None))).first()

    return [
        {
            "id": "first_done_task",
            "code": "first_done_task",
            "title": "Первая выполненная задача",
            "description": "Завершите первую задачу в Komandus.",
            "icon": "check",
            "unlocked_at": done_task.completed_at.isoformat() if done_task and done_task.completed_at else None,
        },
        {
            "id": "ten_done_tasks",
            "code": "ten_done_tasks",
            "title": "10 закрытых задач",
            "description": f"Закрыто задач: {done_count}/10.",
            "icon": "target",
            "unlocked_at": _utc_now_naive().isoformat() if done_count >= 10 else None,
        },
        {
            "id": "ai_flow",
            "code": "ai_flow",
            "title": "AI-поток задач",
            "description": "Получите задачу, извлеченную AI из рабочего контекста.",
            "icon": "sparkles",
            "unlocked_at": ai_task.created_at.isoformat() if ai_task and ai_task.created_at else None,
        },
    ]


@router.get("/users/{user_id}/recommendations")
async def get_recommendations(user_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Recommendations are available only for the current user")

    employee = _find_employee(db, current_user)
    now = _utc_now_naive()
    tasks_query = _user_tasks_query(db, current_user, employee)
    active_count = tasks_query.filter(~KomandusTask.status.in_(CLOSED_STATUSES)).count()
    overdue_count = tasks_query.filter(KomandusTask.due_at < now, ~KomandusTask.status.in_(CLOSED_STATUSES)).count()
    pending_count = tasks_query.filter(KomandusTask.status == TaskStatus.PENDING_CONFIRMATION.value).count()

    recommendations = []
    if overdue_count:
        recommendations.append({
            "id": "overdue-focus",
            "title": "Разберите просроченные задачи",
            "description": f"У вас {overdue_count} просроченных задач. Начните с уточнения дедлайнов и статусов.",
            "recommendation_type": "practice",
            "source": "komandus_tasks",
            "created_at": now.isoformat(),
        })
    if pending_count:
        recommendations.append({
            "id": "confirm-ai-tasks",
            "title": "Подтвердите AI-задачи",
            "description": f"{pending_count} задач ожидают подтверждения, чтобы попасть в рабочий поток.",
            "recommendation_type": "practice",
            "source": "komandus_tasks",
            "created_at": now.isoformat(),
        })
    if active_count == 0:
        recommendations.append({
            "id": "create-first-task",
            "title": "Создайте первую задачу",
            "description": "Добавьте рабочую задачу или подключите источники, чтобы профиль начал наполняться реальными метриками.",
            "recommendation_type": "documentation",
            "source": "komandus_tasks",
            "created_at": now.isoformat(),
        })
    if not recommendations:
        recommendations.append({
            "id": "keep-flow",
            "title": "Поддерживайте актуальные статусы",
            "description": "Регулярно обновляйте статусы задач — так дайджест и аналитика останутся точными.",
            "recommendation_type": "practice",
            "source": "komandus_tasks",
            "created_at": now.isoformat(),
        })
    return recommendations
