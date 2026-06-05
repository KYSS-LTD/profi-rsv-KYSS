from uuid import UUID
from sqlalchemy.orm import Session
from app.common.enums import Role
from app.models.models import KomandusTask, User


class V2TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_org(self, organization_id: UUID):
        return self.db.query(KomandusTask).filter(KomandusTask.organization_id == organization_id).order_by(KomandusTask.created_at.desc()).all()

    def list_for_user(self, user: User):
        query = self.db.query(KomandusTask)
        if user.role != Role.SUPER_ADMIN.value:
            query = query.filter(KomandusTask.organization_id == user.organization_id)
        if user.role == Role.EMPLOYEE.value:
            from app.models.models import Employee
            employee = self.db.query(Employee).filter(Employee.user_id == user.id).first()
            query = query.filter(KomandusTask.employee_id == (employee.id if employee else None))
        elif user.role == Role.DEPARTMENT_MANAGER.value and user.department_id:
            query = query.filter(KomandusTask.department_id == user.department_id)
        elif user.role == Role.PRODUCT_MANAGER.value:
            if user.department_id:
                query = query.filter(KomandusTask.department_id == user.department_id)
            if user.team_id:
                query = query.filter(KomandusTask.team_id == user.team_id)
        return query.order_by(KomandusTask.created_at.desc()).all()

    def get_scoped(self, task_id: UUID, organization_id: UUID, role: str):
        query = self.db.query(KomandusTask).filter(KomandusTask.id == task_id)
        if role != Role.SUPER_ADMIN.value:
            query = query.filter(KomandusTask.organization_id == organization_id)
        return query.first()

    def save(self, task: KomandusTask):
        self.db.add(task); self.db.commit(); self.db.refresh(task)
        return task
