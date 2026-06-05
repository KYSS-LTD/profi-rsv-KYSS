from __future__ import annotations

from collections import Counter, defaultdict
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.enums import TaskStatus
from app.models.models import Employee, KomandusTask, TaskConfirmation


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def dashboard(self, user):
        tasks = self.db.query(KomandusTask).filter(KomandusTask.organization_id == user.organization_id).all()
        total = len(tasks)
        completed = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
        overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
        accepted = sum(1 for task in tasks if task.accepted_at is not None or task.status in {TaskStatus.ACCEPTED.value, TaskStatus.TO_DO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.REVIEW.value, TaskStatus.DONE.value})
        rejected = sum(1 for task in tasks if task.status == TaskStatus.REJECTED.value)
        status_counts = Counter(task.status for task in tasks)
        by_employee = Counter(str(task.employee_id) for task in tasks if task.employee_id)
        closed_by_day = Counter(task.completed_at.date().isoformat() for task in tasks if task.completed_at)
        running = 0
        burnup = []
        for day in sorted(closed_by_day):
            running += closed_by_day[day]
            burnup.append({"date": day, "completed_total": running})
        completion_hours = [((task.completed_at - task.created_at).total_seconds() / 3600) for task in tasks if task.completed_at]
        response_hours = [((task.accepted_at - task.created_at).total_seconds() / 3600) for task in tasks if task.accepted_at]
        return {
            "total_tasks": total,
            "completed": completed,
            "overdue": overdue,
            "average_completion_time": round(sum(completion_hours) / len(completion_hours), 2) if completion_hours else 0,
            "average_response_time": round(sum(response_hours) / len(response_hours), 2) if response_hours else 0,
            "acceptance_percent": round(accepted / total * 100, 2) if total else 0,
            "rejection_percent": round(rejected / total * 100, 2) if total else 0,
            "pie_statuses": dict(status_counts),
            "top_employees": [{"employee_id": employee_id, "tasks": count} for employee_id, count in by_employee.most_common(10)],
            "closed_by_day": [{"date": day, "completed": count} for day, count in sorted(closed_by_day.items())],
            "burnup": burnup,
        }

    def employee(self, employee_id: UUID, user):
        employee = self.db.query(Employee).filter(Employee.id == employee_id, Employee.organization_id == user.organization_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        tasks = self.db.query(KomandusTask).filter(KomandusTask.employee_id == employee_id, KomandusTask.organization_id == user.organization_id).all()
        accepted = sum(1 for task in tasks if task.accepted_at or task.status != TaskStatus.REJECTED.value)
        rejected = sum(1 for task in tasks if task.status == TaskStatus.REJECTED.value)
        completed = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
        overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
        completion_hours = [((task.completed_at - task.created_at).total_seconds() / 3600) for task in tasks if task.completed_at]
        response_hours = [((task.accepted_at - task.created_at).total_seconds() / 3600) for task in tasks if task.accepted_at]
        score = (completed / (overdue * 2 + 1)) * accepted
        ranking = self._ranking(user.organization_id)
        return {
            "employee_id": employee_id,
            "accepted_tasks": accepted,
            "rejected_tasks": rejected,
            "completed_tasks": completed,
            "overdue_tasks": overdue,
            "average_completion_time": round(sum(completion_hours) / len(completion_hours), 2) if completion_hours else 0,
            "average_response_time": round(sum(response_hours) / len(response_hours), 2) if response_hours else 0,
            "efficiency_score": round(score, 2),
            "organization_rank": ranking.get(str(employee_id), 0),
        }

    def _ranking(self, organization_id):
        employees = self.db.query(Employee).filter(Employee.organization_id == organization_id).all()
        scored = []
        for employee in employees:
            tasks = self.db.query(KomandusTask).filter(KomandusTask.employee_id == employee.id).all()
            accepted = sum(1 for task in tasks if task.status != TaskStatus.REJECTED.value)
            completed = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
            overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
            scored.append((str(employee.id), (completed / (overdue * 2 + 1)) * accepted))
        return {employee_id: index + 1 for index, (employee_id, _) in enumerate(sorted(scored, key=lambda row: row[1], reverse=True))}
