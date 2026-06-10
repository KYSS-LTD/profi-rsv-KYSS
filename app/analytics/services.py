from __future__ import annotations

from collections import Counter
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.assistant import AIAssistantService
from app.common.access_scope import AccessScopeService
from app.common.enums import TaskStatus
from app.models.models import Department, Employee, KomandusTask, BoardIntegration


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.scope = AccessScopeService(db)

    def dashboard(self, user, organization_id: UUID | None = None, department_id: UUID | None = None, team_id: UUID | None = None, employee_id: UUID | None = None):
        query = self.scope.get_visible_tasks(user)
        if organization_id:
            query = query.filter(KomandusTask.organization_id == organization_id)
        if department_id:
            query = query.filter(KomandusTask.department_id == department_id)
        if team_id:
            query = query.filter(KomandusTask.team_id == team_id)
        if employee_id:
            query = query.filter(KomandusTask.employee_id == employee_id)
        tasks = query.all()
        visible_employees = self.scope.get_visible_employees(user).all()
        employees = {employee.id: employee for employee in visible_employees}
        departments = {department.id: department for department in self.scope.get_visible_departments(user).all()}
        total = len(tasks)
        in_work = sum(1 for task in tasks if task.status in {TaskStatus.ACCEPTED.value, TaskStatus.TO_DO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.REVIEW.value})
        completed = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
        overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
        rejected = sum(1 for task in tasks if task.status == TaskStatus.REJECTED.value)
        accepted = sum(1 for task in tasks if task.accepted_at is not None or task.status in {TaskStatus.ACCEPTED.value, TaskStatus.TO_DO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.REVIEW.value, TaskStatus.DONE.value})
        ai_tasks = [task for task in tasks if task.llm_confidence is not None]
        status_counts = Counter(task.status for task in tasks)
        by_employee = Counter(task.employee_id for task in tasks if task.employee_id)
        closed_by_day = Counter(task.completed_at.date().isoformat() for task in tasks if task.completed_at)
        running = 0
        burnup = []
        for day in sorted(closed_by_day):
            running += closed_by_day[day]
            burnup.append({"date": day, "completed_total": running})
        completion_hours = [((task.completed_at - task.created_at).total_seconds() / 3600) for task in tasks if task.completed_at]
        response_hours = [((task.accepted_at - task.created_at).total_seconds() / 3600) for task in tasks if task.accepted_at]
        attention = []
        if overdue:
            attention.append({"type": "overdue", "title": "Просроченные задачи", "count": overdue})
        if rejected:
            attention.append({"type": "rejections", "title": "Отказы сотрудников", "count": rejected})
        unassigned = sum(1 for task in tasks if not task.employee_id)
        if unassigned:
            attention.append({"type": "unassigned", "title": "Задачи без исполнителя", "count": unassigned})
        inactive_integrations = self.db.query(BoardIntegration).filter(BoardIntegration.organization_id == user.organization_id, BoardIntegration.is_active.is_(False)).count()
        if inactive_integrations:
            attention.append({"type": "integration", "title": "Ошибки интеграций", "count": inactive_integrations})
        activity = []
        for task in sorted(tasks, key=lambda item: item.updated_at, reverse=True)[:8]:
            employee_name = employees.get(task.employee_id).full_name if task.employee_id in employees else "AI"
            activity.append({"at": task.updated_at.isoformat(), "text": f"{employee_name}: {task.title} → {task.status}"})
        return {
            "total_tasks": total,
            "in_work": in_work,
            "completed": completed,
            "overdue": overdue,
            "average_completion_time": round(sum(completion_hours) / len(completion_hours), 2) if completion_hours else 0,
            "average_response_time": round(sum(response_hours) / len(response_hours), 2) if response_hours else 0,
            "ai_accuracy": round((sum(task.llm_confidence or 0 for task in ai_tasks) / len(ai_tasks)) * 100, 1) if ai_tasks else 0,
            "ai_tasks": len(ai_tasks),
            "acceptance_percent": round(accepted / total * 100, 2) if total else 0,
            "rejection_percent": round(rejected / total * 100, 2) if total else 0,
            "pie_statuses": dict(status_counts),
            "top_employees": [{"employee_id": str(emp_id), "employee_name": employees.get(emp_id).full_name if emp_id in employees else "Не назначен", "tasks": count} for emp_id, count in by_employee.most_common(10)],
            "departments": [{"department_id": str(dept_id), "department_name": departments.get(dept_id).name if dept_id in departments else "Без отдела", "tasks": count} for dept_id, count in Counter(task.department_id for task in tasks if task.department_id).items()],
            "closed_by_day": [{"date": day, "completed": count} for day, count in sorted(closed_by_day.items())],
            "burnup": burnup,
            "attention": attention,
            "activity": activity,
        }

    def employee(self, employee_id: UUID, user):
        employee = self.scope.get_visible_employees(user).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        tasks = self.scope.get_visible_tasks(user).filter(KomandusTask.employee_id == employee_id).all()
        accepted = sum(1 for task in tasks if task.accepted_at or task.status != TaskStatus.REJECTED.value)
        rejected = sum(1 for task in tasks if task.status == TaskStatus.REJECTED.value)
        completed = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
        overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
        completion_hours = [((task.completed_at - task.created_at).total_seconds() / 3600) for task in tasks if task.completed_at]
        response_hours = [((task.accepted_at - task.created_at).total_seconds() / 3600) for task in tasks if task.accepted_at]
        score = (completed / (overdue * 2 + 1)) * accepted
        ranking = self._ranking(user)
        return {"employee_id": employee_id, "employee_name": employee.full_name, "accepted_tasks": accepted, "rejected_tasks": rejected, "completed_tasks": completed, "overdue_tasks": overdue, "average_completion_time": round(sum(completion_hours) / len(completion_hours), 2) if completion_hours else 0, "average_response_time": round(sum(response_hours) / len(response_hours), 2) if response_hours else 0, "efficiency_score": round(score, 2), "organization_rank": ranking.get(str(employee_id), 0)}

    def ai_assistant(self, user, question: str):
        return AIAssistantService(self.db).fallback_answer(user, question)

    def _ranking(self, user):
        scored = []
        for employee in self.scope.get_visible_employees(user).all():
            tasks = self.scope.get_visible_tasks(user).filter(KomandusTask.employee_id == employee.id).all()
            accepted = sum(1 for task in tasks if task.status != TaskStatus.REJECTED.value)
            completed = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
            overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
            scored.append((str(employee.id), (completed / (overdue * 2 + 1)) * accepted))
        return {employee_id: index + 1 for index, (employee_id, _) in enumerate(sorted(scored, key=lambda row: row[1], reverse=True))}
