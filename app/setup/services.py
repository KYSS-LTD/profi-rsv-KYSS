from __future__ import annotations

import re

from fastapi import HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.repositories import UserRepository
from app.auth.services import AuthService
from app.common.enums import Role
from app.common.security import hash_password
from app.common.rbac import scopes_for_role
from app.models.models import Organization, User
from app.organizations.repositories import OrganizationRepository
from app.setup.schemas import SetupRequest


class SetupService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.organizations = OrganizationRepository(db)

    def is_initialized(self) -> bool:
        return self.users.count() > 0

    def initialize(self, payload: SetupRequest, response: Response):
        try:
            self._lock_users_table_for_setup()
            if self.is_initialized():
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System already initialized")

            organization = Organization(name=payload.organization_name.strip(), slug=self._make_unique_slug(payload.organization_name))
            self.organizations.add(organization)
            self.db.flush()
            user = User(
                organization_id=organization.id,
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
                full_name=payload.full_name.strip(),
                role=Role.OWNER.value,
                permission_scopes=sorted(scope.value for scope in scopes_for_role(Role.OWNER)),
                is_active=True,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        except HTTPException:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise

        return AuthService(self.db).issue_tokens_for_user(user, response, audit_action="Initial Setup")

    def _lock_users_table_for_setup(self) -> None:
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            self.db.execute(text("LOCK TABLE users IN EXCLUSIVE MODE"))

    def _make_unique_slug(self, name: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "organization"
        slug = base[:120]
        suffix = 2
        while self.organizations.get_by_slug(slug):
            suffix_text = f"-{suffix}"
            slug = f"{base[: 128 - len(suffix_text)]}{suffix_text}"
            suffix += 1
        return slug
