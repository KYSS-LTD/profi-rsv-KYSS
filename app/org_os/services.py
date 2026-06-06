from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.access_scope import AccessScopeService
from app.common.enums import PermissionScope, Role, TaskStatus
from app.common.rbac import normalize_role
from app.models.models import Delegation, Employee, KomandusTask, OrganizationalEvent, ResponsibilityArea, Successor, User
from app.org_os.schemas import AttentionItem, HealthScore, OrganizationMapNode, ProfileContextResponse, WorkloadSummary


ACTIVE_STATUSES = {TaskStatus.ACCEPTED.value, TaskStatus.TO_DO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.REVIEW.value, TaskStatus.PENDING_CONFIRMATION.value}


class OrgOSService:
    def __init__(self, db: Session):
        self.db = db
        self.scope = AccessScopeService(db)

    def organization_map(self, user) -> dict:
        employees = self.scope.get_visible_employees(user).order_by(Employee.full_name.asc()).all()
        tasks = self.scope.get_visible_tasks(user).all()
        responsibilities = self._responsibilities(user.organization_id)
        delegations = self._active_delegations(user.organization_id)
        workload_by_employee = self._workload(tasks)
        descendants = self._descendant_counts(employees)
        children: dict[UUID | None, list[Employee]] = defaultdict(list)
        visible_ids = {employee.id for employee in employees}
        for employee in employees:
            parent_id = employee.manager_id if employee.manager_id in visible_ids else None
            children[parent_id].append(employee)

        def build(employee: Employee) -> OrganizationMapNode:
            workload = workload_by_employee.get(employee.id, WorkloadSummary(active_tasks=0, overdue_tasks=0, blocked_tasks=0, completed_tasks=0, workload_score=0))
            owned = responsibilities.get(employee.user_id, []) if employee.user_id else []
            node_children = [build(child) for child in children.get(employee.id, [])]
            return OrganizationMapNode(
                id=employee.id,
                user_id=employee.user_id,
                full_name=employee.full_name,
                position=employee.position,
                role=normalize_role(employee.role).value,
                manager_id=employee.manager_id,
                department_id=employee.department_id,
                team_id=employee.team_id,
                direct_reports=len(children.get(employee.id, [])),
                indirect_reports=descendants.get(employee.id, 0),
                responsibilities=owned,
                active_delegations=delegations.get(employee.user_id, 0) if employee.user_id else 0,
                workload=workload,
                requires_attention=workload.overdue_tasks > 0 or workload.workload_score >= 80 or bool(owned),
                children=node_children,
            )

        roots = [build(employee) for employee in children.get(None, [])]
        attention = self.attention(user, employees=employees, tasks=tasks)
        return {
            "nodes": roots,
            "attention": attention,
            "health": self.health_score(employees, tasks, attention),
            "role_model": [role.value for role in Role],
            "permission_scopes": [scope.value for scope in PermissionScope],
        }

    def profile_context(self, user, employee_id: UUID) -> ProfileContextResponse:
        employees = self.scope.get_visible_employees(user).all()
        by_id = {employee.id: employee for employee in employees}
        employee = by_id.get(employee_id)
        if not employee:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Employee not found")
        tree = self.organization_map(user)
        flat = self._flatten_nodes(tree["nodes"])
        node = next(item for item in flat if item.id == employee_id)
        direct = [candidate.full_name for candidate in employees if candidate.manager_id == employee_id]
        delegations = self.db.query(Delegation).filter(Delegation.organization_id == user.organization_id, or_(Delegation.delegator_id == employee.user_id, Delegation.delegate_id == employee.user_id)).all() if employee.user_id else []
        successors = self.db.query(Successor).filter(Successor.organization_id == user.organization_id, Successor.subject_user_id == employee.user_id, Successor.status == "ACTIVE").all() if employee.user_id else []
        users = {item.id: item.full_name or item.email for item in self.db.query(User).filter(User.organization_id == user.organization_id).all()}
        events = self.db.query(OrganizationalEvent).filter(OrganizationalEvent.organization_id == user.organization_id, OrganizationalEvent.entity_id == str(employee_id)).order_by(OrganizationalEvent.occurred_at.desc()).limit(5).all()
        return ProfileContextResponse(
            employee=node,
            reports_to=by_id[employee.manager_id].full_name if employee.manager_id in by_id else None,
            direct_reports=direct,
            indirect_reports=node.indirect_reports,
            responsibilities=node.responsibilities,
            delegations=[f"{users.get(item.delegator_id, 'Делегирующий')} → {users.get(item.delegate_id, 'Делегат')} до {item.end_date.date()}" for item in delegations],
            successors=[users.get(item.successor_user_id, str(item.successor_user_id)) for item in successors],
            recent_activity=[f"{event.event_type}: {event.entity_type or ''}" for event in events],
        )

    def attention(self, user, *, employees: list[Employee] | None = None, tasks: list[KomandusTask] | None = None) -> list[AttentionItem]:
        employees = employees if employees is not None else self.scope.get_visible_employees(user).all()
        tasks = tasks if tasks is not None else self.scope.get_visible_tasks(user).all()
        workload = self._workload(tasks)
        overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
        unowned = sum(1 for task in tasks if not task.employee_id and not task.current_owner_user_id and not task.assigned_position_id and not task.assigned_organizational_unit_id and not task.assigned_responsibility_area_id)
        no_deadline = sum(1 for task in tasks if task.due_at is None and task.status not in {TaskStatus.DONE.value, TaskStatus.REJECTED.value})
        overloaded = sum(1 for employee in employees if workload.get(employee.id) and workload[employee.id].workload_score >= 80)
        bottlenecks = sum(1 for task in tasks if task.status == TaskStatus.REVIEW.value)
        items = []
        if overdue:
            items.append(AttentionItem(type="overdue_tasks", title="Просроченные задачи", count=overdue, severity="critical", explanation="Нужно эскалировать по цепочке руководителей или активной делегации."))
        if overloaded:
            items.append(AttentionItem(type="overloaded_people", title="Перегруженные сотрудники", count=overloaded, severity="warning", explanation="Нагрузка выше безопасного порога: перераспределите владельцев или сроки."))
        if unowned:
            items.append(AttentionItem(type="tasks_without_owner", title="Задачи без владельца", count=unowned, severity="warning", explanation="Назначьте пользователя, позицию, орг-единицу или зону ответственности."))
        if no_deadline:
            items.append(AttentionItem(type="tasks_without_deadline", title="Задачи без срока", count=no_deadline, severity="info", explanation="Без сроков система не сможет корректно эскалировать работу."))
        if bottlenecks:
            items.append(AttentionItem(type="approval_bottlenecks", title="Узкие места согласований", count=bottlenecks, severity="warning", explanation="Проверьте цепочку согласования, делегации и преемников."))
        return items

    def health_score(self, employees: list[Employee], tasks: list[KomandusTask], attention: list[AttentionItem]) -> HealthScore:
        if not tasks and not employees:
            return HealthScore(score=100, causes=["Организация пока не содержит сотрудников и задач."])
        overdue_rate = (sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value) / max(1, len(tasks)))
        blocked_rate = (sum(1 for task in tasks if task.status == TaskStatus.REVIEW.value) / max(1, len(tasks)))
        span_penalty = sum(1 for employee_id, count in Counter(employee.manager_id for employee in employees if employee.manager_id).items() if count > 8) * 5
        score = max(0, min(100, round(100 - overdue_rate * 35 - blocked_rate * 20 - len(attention) * 5 - span_penalty)))
        causes = ["Оценка учитывает просрочку, блокировки, перегрузку и размер команды у руководителей."]
        if overdue_rate:
            causes.append(f"Доля просрочки: {round(overdue_rate * 100, 1)}%.")
        if blocked_rate:
            causes.append(f"Задачи на согласовании/блокировке: {round(blocked_rate * 100, 1)}%.")
        if span_penalty:
            causes.append("Есть руководители со слишком широким span of control.")
        return HealthScore(score=score, causes=causes)

    def _workload(self, tasks: list[KomandusTask]) -> dict[UUID, WorkloadSummary]:
        result: dict[UUID, WorkloadSummary] = {}
        grouped: dict[UUID, list[KomandusTask]] = defaultdict(list)
        for task in tasks:
            if task.employee_id:
                grouped[task.employee_id].append(task)
        for employee_id, items in grouped.items():
            active = sum(1 for task in items if task.status in ACTIVE_STATUSES)
            overdue = sum(1 for task in items if task.status == TaskStatus.OVERDUE.value)
            blocked = sum(1 for task in items if task.status == TaskStatus.REVIEW.value)
            completed = sum(1 for task in items if task.status == TaskStatus.DONE.value)
            score = min(100, active * 12 + overdue * 20 + blocked * 10)
            result[employee_id] = WorkloadSummary(active_tasks=active, overdue_tasks=overdue, blocked_tasks=blocked, completed_tasks=completed, workload_score=score)
        return result

    def _responsibilities(self, organization_id: UUID) -> dict[UUID, list[str]]:
        rows = self.db.query(ResponsibilityArea).filter(ResponsibilityArea.organization_id == organization_id, ResponsibilityArea.status == "ACTIVE").all()
        result: dict[UUID, list[str]] = defaultdict(list)
        for row in rows:
            if row.owner_user_id:
                result[row.owner_user_id].append(row.name)
            if row.backup_owner_id:
                result[row.backup_owner_id].append(f"Резерв: {row.name}")
        return result

    def _active_delegations(self, organization_id: UUID) -> dict[UUID, int]:
        now = datetime.utcnow()
        rows = self.db.query(Delegation).filter(Delegation.organization_id == organization_id, Delegation.start_date <= now, Delegation.end_date >= now, Delegation.status.in_(["ACTIVE", "SCHEDULED"])).all()
        result: dict[UUID, int] = defaultdict(int)
        for row in rows:
            result[row.delegator_id] += 1
            result[row.delegate_id] += 1
        return result

    def _descendant_counts(self, employees: list[Employee]) -> dict[UUID, int]:
        children: dict[UUID | None, list[Employee]] = defaultdict(list)
        for employee in employees:
            children[employee.manager_id].append(employee)
        counts = {}
        def count(employee_id: UUID) -> int:
            total = 0
            for child in children.get(employee_id, []):
                total += 1 + count(child.id)
            return total
        for employee in employees:
            counts[employee.id] = count(employee.id)
        return counts

    def _flatten_nodes(self, nodes: list[OrganizationMapNode]) -> list[OrganizationMapNode]:
        flat = []
        stack = list(nodes)
        while stack:
            node = stack.pop()
            flat.append(node)
            stack.extend(node.children)
        return flat
