from uuid import UUID
from sqlalchemy.orm import Session
from app.common.enums import Role
from app.models.models import KomandusTask


class V2TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_org(self, organization_id: UUID):
        return self.db.query(KomandusTask).filter(KomandusTask.organization_id == organization_id).order_by(KomandusTask.created_at.desc()).all()

    def get_scoped(self, task_id: UUID, organization_id: UUID, role: str):
        query = self.db.query(KomandusTask).filter(KomandusTask.id == task_id)
        if role != Role.SUPER_ADMIN.value:
            query = query.filter(KomandusTask.organization_id == organization_id)
        return query.first()

    def save(self, task: KomandusTask):
        self.db.add(task); self.db.commit(); self.db.refresh(task)
        return task
