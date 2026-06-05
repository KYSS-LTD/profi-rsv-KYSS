from __future__ import annotations

from collections import Counter
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.enums import TaskStatus
from app.models.models import Department, Employee, KomandusTask, OrganizationChat, BoardIntegration


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def dashboard(self, user):
        tasks = self._task_query(user).all()
        employees = {employee.id: employee for employee in self.db.query(Employee).filter(Employee.organization_id == user.organization_id).all()}
        departments = {department.id: department for department in self.db.query(Department).filter(Department.organization_id == user.organization_id).all()}
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
            "top_employees": [{"employee_id": str(employee_id), "employee_name": employees.get(employee_id).full_name if employee_id in employees else "Не назначен", "tasks": count} for employee_id, count in by_employee.most_common(10)],
            "departments": [{"department_id": str(dept_id), "department_name": departments.get(dept_id).name if dept_id in departments else "Без отдела", "tasks": count} for dept_id, count in Counter(task.department_id for task in tasks if task.department_id).items()],
            "closed_by_day": [{"date": day, "completed": count} for day, count in sorted(closed_by_day.items())],
            "burnup": burnup,
            "attention": attention,
            "activity": activity,
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
            "employee_name": employee.full_name,
            "accepted_tasks": accepted,
            "rejected_tasks": rejected,
            "completed_tasks": completed,
            "overdue_tasks": overdue,
            "average_completion_time": round(sum(completion_hours) / len(completion_hours), 2) if completion_hours else 0,
            "average_response_time": round(sum(response_hours) / len(response_hours), 2) if response_hours else 0,
            "efficiency_score": round(score, 2),
            "organization_rank": ranking.get(str(employee_id), 0),
        }

    def ai_assistant(self, user, question: str):
        data = self.dashboard(user)
        facts = [
            f"Всего задач: {data['total_tasks']}",
            f"Просрочено: {data['overdue']}",
            f"В работе: {data['in_work']}",
            f"AI accuracy: {data['ai_accuracy']}%",
            f"Отказы: {data['rejection_percent']}%",
        ]
        lower = question.lower()
        if "перегруж" in lower:
            leader = next(iter(data["top_employees"]), None)
            answer = f"Самая высокая нагрузка сейчас у {leader['employee_name']} — {leader['tasks']} задач." if leader else "Нагрузка пока не выявлена: задач нет."
        elif "срок" in lower or "рис" in lower:
            answer = f"Главный риск — {data['overdue']} просроченных задач и {sum(1 for item in data['attention'] if item['type'] == 'unassigned')} групп задач без исполнителя."
        else:
            answer = f"За период в системе {data['total_tasks']} задач, {data['completed']} завершено, {data['in_work']} в работе. Требуют внимания: {len(data['attention'])} сигналов."
        return {"answer": answer, "facts": facts}

    def _task_query(self, user):
        query = self.db.query(KomandusTask)
        if user.role != "SUPER_ADMIN":
            query = query.filter(KomandusTask.organization_id == user.organization_id)
        if user.role == "DEPARTMENT_MANAGER" and user.department_id:
            query = query.filter(KomandusTask.department_id == user.department_id)
        return query

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
