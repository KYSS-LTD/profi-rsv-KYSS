from __future__ import annotations

import hashlib
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.boards.schemas import BoardMappingCreate, ColumnMappingCreate, EmployeeBoardMappingCreate, VerifyYouGileRequest
from app.common.security import encrypt_secret
from app.common.access_scope import AccessScopeService
from app.common.enums import OrganizationMode, Role
from app.common.rbac import normalize_role
from app.models.models import BoardIntegration, BoardMapping, ColumnMapping, EmployeeBoardMapping, Organization, Team, ProcessedWebhookEvent
from app.yougile.provider import YouGileProvider


class BoardService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    async def verify_yougile(self, api_token: str | VerifyYouGileRequest, user):
        payload = api_token if isinstance(api_token, VerifyYouGileRequest) else VerifyYouGileRequest(api_token=api_token)
        self._validate_mapping_scope(payload.department_id, payload.team_id, user)
        metadata = await YouGileProvider(payload.api_token).sync()
        integration = BoardIntegration(organization_id=user.organization_id, provider="yougile", name="YouGile", encrypted_api_token=encrypt_secret(payload.api_token), department_id=payload.department_id, team_id=payload.team_id, metadata_json=metadata)
        self.db.add(integration)
        self.db.commit(); self.db.refresh(integration)
        self.audit.log(action="Connect Board", organization_id=user.organization_id, user_id=user.id, entity_type="BoardIntegration", entity_id=integration.id)
        return integration


    def list_board_mappings(self, user):
        query = self.db.query(BoardMapping).filter(BoardMapping.organization_id == user.organization_id)
        role = normalize_role(user.role)
        if role in {Role.OWNER, Role.ADMIN}:
            return query.order_by(BoardMapping.created_at.desc()).all()
        scope = AccessScopeService(self.db).visible_scope_ids(user)
        return query.filter((BoardMapping.department_id.in_(scope.department_ids)) | (BoardMapping.team_id.in_(scope.team_ids))).order_by(BoardMapping.created_at.desc()).all()

    def create_board_mapping(self, payload: BoardMappingCreate, user):
        self._validate_mapping_scope(payload.department_id, payload.team_id, user)
        if payload.board_integration_id:
            self._get_integration(payload.board_integration_id, user)
        mapping = BoardMapping(
            organization_id=user.organization_id,
            provider="yougile",
            department_id=payload.department_id,
            team_id=payload.team_id,
            board_integration_id=payload.board_integration_id,
            external_project_id=payload.external_project_id,
            external_board_id=payload.external_board_id,
            external_board_name=payload.external_board_name,
            status="ACTIVE",
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        self.audit.log(action="Create Board Mapping", organization_id=user.organization_id, user_id=user.id, entity_type="BoardMapping", entity_id=mapping.id)
        return mapping

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


    def _validate_mapping_scope(self, department_id: UUID | None, team_id: UUID | None, user) -> None:
        role = normalize_role(user.role)
        if role in {Role.OWNER, Role.ADMIN}:
            return
        if role != Role.MANAGER:
            raise HTTPException(status_code=403, detail="Only owners, admins, and managers can map boards")
        organization = self.db.query(Organization).filter(Organization.id == user.organization_id).first()
        if (not organization or organization.org_mode == OrganizationMode.SIMPLE.value) and not department_id and not team_id:
            return
        scope = AccessScopeService(self.db).visible_scope_ids(user)
        if team_id:
            team = self.db.query(Team).filter(Team.id == team_id, Team.organization_id == user.organization_id).first()
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            if team.id in scope.team_ids or team.department_id in scope.department_ids:
                return
        if department_id and department_id in scope.department_ids:
            return
        raise HTTPException(status_code=403, detail="Board mapping is outside manager visibility branch")

    def _get_integration(self, integration_id: UUID, user):
        integration = self.db.query(BoardIntegration).filter(BoardIntegration.id == integration_id, BoardIntegration.organization_id == user.organization_id).first()
        if not integration:
            raise HTTPException(status_code=404, detail="Board integration not found")
        return integration
