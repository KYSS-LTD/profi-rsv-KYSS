from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Query, Session

from app.common.enums import Role
from app.common.rbac import normalize_role
from app.models.models import Department, Employee, KomandusTask, Team, User


@dataclass(frozen=True)
class ScopeIds:
    employee_ids: set[UUID]
    department_ids: set[UUID]
    team_ids: set[UUID]


class AccessScopeService:
    """Computes tenant and hierarchy-aware data visibility for RBAC.

    Managers are scoped through the employee.manager_id tree first and then
    constrained to their department/team where applicable, preventing access to
    parallel departments or teams.
    """

    def __init__(self, db: Session):
        self.db = db

    def current_employee(self, user: User) -> Employee | None:
        return self.db.query(Employee).filter(Employee.user_id == user.id, Employee.is_active.is_(True)).first()

    def get_visible_employees(self, user: User) -> Query:
        query = self.db.query(Employee)
        role = normalize_role(user.role)
        if role == Role.SUPER_ADMIN:
            return query
        query = query.filter(Employee.organization_id == user.organization_id)
        ids = self._visible_employee_ids(user)
        if ids is not None:
            query = query.filter(Employee.id.in_(ids) if ids else False)
        return query

    def get_visible_departments(self, user: User) -> Query:
        query = self.db.query(Department)
        role = normalize_role(user.role)
        if role == Role.SUPER_ADMIN:
            return query
        query = query.filter(Department.organization_id == user.organization_id)
        if role == Role.DEPARTMENT_MANAGER and user.department_id:
            query = query.filter(Department.id == user.department_id)
        elif role == Role.TEAM_LEAD:
            employee = self.current_employee(user)
            dept_id = user.department_id or (employee.department_id if employee else None)
            query = query.filter(Department.id == dept_id) if dept_id else query.filter(False)
        elif role in {Role.EMPLOYEE, Role.VIEWER}:
            employee = self.current_employee(user)
            dept_id = user.department_id or (employee.department_id if employee else None)
            query = query.filter(Department.id == dept_id) if dept_id else query.filter(False)
        return query

    def get_visible_teams(self, user: User) -> Query:
        query = self.db.query(Team)
        role = normalize_role(user.role)
        if role == Role.SUPER_ADMIN:
            return query
        query = query.filter(Team.organization_id == user.organization_id)
        if role == Role.DEPARTMENT_MANAGER and user.department_id:
            query = query.filter(Team.department_id == user.department_id)
        elif role == Role.TEAM_LEAD:
            employee = self.current_employee(user)
            team_id = user.team_id or (employee.team_id if employee else None)
            query = query.filter(Team.id == team_id) if team_id else query.filter(False)
        elif role in {Role.EMPLOYEE, Role.VIEWER}:
            employee = self.current_employee(user)
            team_id = user.team_id or (employee.team_id if employee else None)
            query = query.filter(Team.id == team_id) if team_id else query.filter(False)
        return query

    def get_visible_tasks(self, user: User) -> Query:
        query = self.db.query(KomandusTask)
        role = normalize_role(user.role)
        if role == Role.SUPER_ADMIN:
            return query
        query = query.filter(KomandusTask.organization_id == user.organization_id)
        if role in {Role.ORG_OWNER, Role.PRODUCT_MANAGER}:
            if role == Role.PRODUCT_MANAGER:
                if user.department_id:
                    query = query.filter(KomandusTask.department_id == user.department_id)
                if user.team_id:
                    query = query.filter(KomandusTask.team_id == user.team_id)
            return query
        ids = self._visible_employee_ids(user)
        return query.filter(KomandusTask.employee_id.in_(ids) if ids else False)

    def visible_scope_ids(self, user: User) -> ScopeIds:
        employees = self.get_visible_employees(user).all()
        return ScopeIds(
            employee_ids={employee.id for employee in employees},
            department_ids={employee.department_id for employee in employees if employee.department_id},
            team_ids={employee.team_id for employee in employees if employee.team_id},
        )

    def can_access_employee(self, user: User, employee_id: UUID) -> bool:
        role = normalize_role(user.role)
        if role == Role.SUPER_ADMIN:
            return True
        ids = self._visible_employee_ids(user)
        return ids is None or employee_id in ids

    def _visible_employee_ids(self, user: User) -> set[UUID] | None:
        role = normalize_role(user.role)
        if role in {Role.SUPER_ADMIN, Role.ORG_OWNER, Role.PRODUCT_MANAGER}:
            return None
        current = self.current_employee(user)
        if not current:
            return set()
        all_employees = self.db.query(Employee).filter(Employee.organization_id == current.organization_id).all()
        children: dict[UUID | None, list[Employee]] = {}
        for employee in all_employees:
            children.setdefault(employee.manager_id, []).append(employee)
        visible: set[UUID] = set()
        stack = [current]
        while stack:
            employee = stack.pop()
            if employee.id in visible:
                continue
            visible.add(employee.id)
            stack.extend(children.get(employee.id, []))
        if role == Role.DEPARTMENT_MANAGER:
            dept_id = user.department_id or current.department_id
            visible = {employee.id for employee in all_employees if employee.id in visible and employee.department_id == dept_id}
        elif role == Role.TEAM_LEAD:
            team_id = user.team_id or current.team_id
            visible = {employee.id for employee in all_employees if employee.id in visible and employee.team_id == team_id}
        elif role in {Role.EMPLOYEE, Role.VIEWER}:
            visible = {current.id}
        return visible
