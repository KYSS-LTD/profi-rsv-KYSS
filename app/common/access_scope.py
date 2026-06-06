from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Query, Session

from app.common.enums import OrganizationMode, Role
from app.common.rbac import normalize_role
from app.models.models import Department, Employee, KomandusTask, Organization, Team, User


@dataclass(frozen=True)
class ScopeIds:
    employee_ids: set[UUID]
    department_ids: set[UUID]
    team_ids: set[UUID]


class AccessScopeService:
    """Backend-enforced human visibility.

    Technical roles grant administration rights, while the reporting tree in
    employees.manager_id is the single source of truth for manager visibility.
    """

    def __init__(self, db: Session):
        self.db = db

    def current_employee(self, user: User) -> Employee | None:
        return self.db.query(Employee).filter(Employee.user_id == user.id, Employee.is_active.is_(True)).first()

    def get_visible_employees(self, user: User) -> Query:
        query = self.db.query(Employee)
        role = normalize_role(user.role)
        if role in {Role.OWNER, Role.ADMIN} or self._is_simple_manager(user):
            return query.filter(Employee.organization_id == user.organization_id)
        query = query.filter(Employee.organization_id == user.organization_id)
        ids = self._visible_employee_ids(user)
        return query.filter(Employee.id.in_(ids) if ids else False)

    def get_visible_departments(self, user: User) -> Query:
        query = self.db.query(Department).filter(Department.organization_id == user.organization_id)
        if normalize_role(user.role) in {Role.OWNER, Role.ADMIN, Role.OBSERVER} or self._is_simple_manager(user):
            return query
        scope = self.visible_scope_ids(user)
        return query.filter(Department.id.in_(scope.department_ids) if scope.department_ids else False)

    def get_visible_teams(self, user: User) -> Query:
        query = self.db.query(Team).filter(Team.organization_id == user.organization_id)
        if normalize_role(user.role) in {Role.OWNER, Role.ADMIN, Role.OBSERVER} or self._is_simple_manager(user):
            return query
        scope = self.visible_scope_ids(user)
        return query.filter(Team.id.in_(scope.team_ids) if scope.team_ids else False)

    def get_visible_tasks(self, user: User) -> Query:
        query = self.db.query(KomandusTask).filter(KomandusTask.organization_id == user.organization_id)
        role = normalize_role(user.role)
        if role in {Role.OWNER, Role.ADMIN, Role.OBSERVER} or self._is_simple_manager(user):
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
        if normalize_role(user.role) in {Role.OWNER, Role.ADMIN} or self._is_simple_manager(user):
            return True
        return employee_id in self._visible_employee_ids(user)

    def _visible_employee_ids(self, user: User) -> set[UUID]:
        role = normalize_role(user.role)
        current = self.current_employee(user)
        if not current:
            return set()
        if self._is_simple_manager(user):
            return {employee.id for employee in self.db.query(Employee).filter(Employee.organization_id == user.organization_id).all()}
        if role == Role.EMPLOYEE:
            return {current.id}
        if role == Role.OBSERVER:
            return {employee.id for employee in self.db.query(Employee).filter(Employee.organization_id == user.organization_id).all()}

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
        return visible


    def _is_simple_manager(self, user: User) -> bool:
        if normalize_role(user.role) != Role.MANAGER:
            return False
        organization = self.db.query(Organization).filter(Organization.id == user.organization_id).first()
        return not organization or organization.org_mode == OrganizationMode.SIMPLE.value
