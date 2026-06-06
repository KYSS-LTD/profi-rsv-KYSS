from __future__ import annotations

import hashlib
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.boards.schemas import ColumnMappingCreate, EmployeeBoardMappingCreate, VerifyYouGileRequest
from app.common.security import encrypt_secret
from app.models.models import BoardIntegration, ColumnMapping, EmployeeBoardMapping, ProcessedWebhookEvent
from app.yougile.provider import YouGileProvider


class BoardService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    async def verify_yougile(self, api_token: str | VerifyYouGileRequest, user):
        payload = api_token if isinstance(api_token, VerifyYouGileRequest) else VerifyYouGileRequest(api_token=api_token)
        metadata = await YouGileProvider(payload.api_token).sync()
        integration = BoardIntegration(organization_id=user.organization_id, provider="yougile", name="YouGile", encrypted_api_token=encrypt_secret(payload.api_token), department_id=payload.department_id, team_id=payload.team_id, metadata_json=metadata)
        self.db.add(integration)
        self.db.commit(); self.db.refresh(integration)
        self.audit.log(action="Connect Board", organization_id=user.organization_id, user_id=user.id, entity_type="BoardIntegration", entity_id=integration.id)
        return integration

    def add_column_mapping(self, integration_id: UUID, payload: ColumnMappingCreate, user):
        integration = self._get_integration(integration_id, user)
        mapping = ColumnMapping(organization_id=user.organization_id, board_integration_id=integration.id, task_status=payload.task_status, external_column_id=payload.external_column_id, external_column_name=payload.external_column_name)
        self.db.add(mapping); self.db.commit(); self.db.refresh(mapping)
        return mapping

    def add_employee_mapping(self, integration_id: UUID, payload: EmployeeBoardMappingCreate, user):
        integration = self._get_integration(integration_id, user)
        mapping = EmployeeBoardMapping(organization_id=user.organization_id, board_integration_id=integration.id, employee_id=payload.employee_id, external_user_id=payload.external_user_id, external_email=payload.external_email)
        self.db.add(mapping); self.db.commit(); self.db.refresh(mapping)
        return mapping

    def record_webhook_event(self, provider: str, event_id: str, payload: bytes, user_org):
        payload_hash = hashlib.sha256(payload).hexdigest()
        existing = self.db.query(ProcessedWebhookEvent).filter(ProcessedWebhookEvent.provider == provider, ProcessedWebhookEvent.event_id == event_id).first()
        if existing:
            return False
        self.db.add(ProcessedWebhookEvent(organization_id=user_org, provider=provider, event_id=event_id, payload_hash=payload_hash))
        self.db.commit()
        return True

    def _get_integration(self, integration_id: UUID, user):
        integration = self.db.query(BoardIntegration).filter(BoardIntegration.id == integration_id, BoardIntegration.organization_id == user.organization_id).first()
        if not integration:
            raise HTTPException(status_code=404, detail="Board integration not found")
        return integration
