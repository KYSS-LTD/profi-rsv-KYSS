from uuid import UUID
from sqlalchemy.orm import Session
from app.common.enums import Role
from app.models.models import Employee, User


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_org(self, organization_id: UUID):
        return self.db.query(Employee).filter(Employee.organization_id == organization_id).order_by(Employee.created_at.desc()).all()

    def get_for_org(self, employee_id: UUID, organization_id: UUID, requester_role: str):
        query = self.db.query(Employee).filter(Employee.id == employee_id)
        if requester_role != Role.SUPER_ADMIN.value:
            query = query.filter(Employee.organization_id == organization_id)
        return query.first()

    def save(self, employee: Employee):
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def delete(self, employee: Employee):
        self.db.delete(employee)
        self.db.commit()
