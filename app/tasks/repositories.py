from uuid import UUID
from sqlalchemy.orm import Session

from app.common.access_scope import AccessScopeService
from app.common.enums import Role
from app.common.rbac import normalize_role
from app.models.models import KomandusTask, User


class V2TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_org(self, organization_id: UUID):
        return self.db.query(KomandusTask).filter(KomandusTask.organization_id == organization_id).order_by(KomandusTask.created_at.desc()).all()

    def list_for_user(self, user: User):
        return AccessScopeService(self.db).get_visible_tasks(user).order_by(KomandusTask.created_at.desc()).all()

    def get_scoped(self, task_id: UUID, user: User):
        query = AccessScopeService(self.db).get_visible_tasks(user).filter(KomandusTask.id == task_id)
        return query.first()

    def save(self, task: KomandusTask):
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
