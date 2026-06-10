from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.models import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, *, action: str, organization_id=None, user_id=None, entity_type: str | None = None, entity_id: str | None = None, metadata: dict | None = None, request_id: str | None = None) -> AuditLog:
        entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            metadata_json=metadata,
            request_id=request_id,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
