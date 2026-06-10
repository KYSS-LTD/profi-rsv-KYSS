from __future__ import annotations

import hashlib
from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.auth.magic import MagicLoginService
from app.auth.repositories import UserRepository
from app.common.security import create_jwt, hash_password, verify_password
from app.common.enums import Role
from app.common.rbac import normalize_role
from app.models.models import User
from app.core.config import settings


REFRESH_COOKIE_NAME = "komandus_refresh"


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    def login(self, email: str, password: str, response: Response):
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return self.issue_tokens_for_user(user, response, audit_action="Login")

    def magic_login(self, token: str, response: Response):
        user = MagicLoginService(self.db).consume_token(token)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Magic link is invalid, expired, or already used")
        return self.issue_tokens_for_user(user, response, audit_action="Magic Login")

    def change_password(self, user, new_password: str):
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        self.users.save(user)
        self.audit.log(action="Change Password", organization_id=user.organization_id, user_id=user.id)
        return {"status": "password_changed"}

    def impersonate(self, actor, target_user_id: str, response: Response):
        if normalize_role(actor.role) != Role.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only organization owners can impersonate employees")
        target = self.users.get_by_id(str(target_user_id))
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        if normalize_role(actor.role) != Role.OWNER and target.organization_id != actor.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot impersonate user outside organization")
        target.impersonated_by_user_id = actor.id
        self.users.save(target)
        self.audit.log(action="Impersonate User", organization_id=target.organization_id, user_id=actor.id, entity_type="User", entity_id=target.id)
        return self.issue_tokens_for_user(target, response, audit_action="Impersonation Login")

    def issue_tokens_for_user(self, user, response: Response, *, audit_action: str = "Login"):
        access = create_jwt({"sub": str(user.id), "org": str(user.organization_id), "role": user.role}, settings.JWT_SECRET, settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh = create_jwt({"sub": str(user.id), "typ": "refresh"}, settings.JWT_SECRET, settings.REFRESH_TOKEN_EXPIRE_SECONDS)
        user.refresh_token_hash = hashlib.sha256(refresh.encode()).hexdigest()
        self.users.save(user)
        response.set_cookie(REFRESH_COOKIE_NAME, refresh, max_age=settings.REFRESH_TOKEN_EXPIRE_SECONDS, httponly=True, secure=settings.APP_ENV == "production", samesite="lax")
        self.audit.log(action=audit_action, organization_id=user.organization_id, user_id=user.id)
        return {"access_token": access, "token_type": "bearer", "must_change_password": bool(user.must_change_password)}

    def refresh(self, refresh_token: str | None, response: Response):
        from app.common.security import decode_jwt
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token")
        payload = decode_jwt(refresh_token, settings.JWT_SECRET)
        if payload.get("typ") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user = self.users.get_by_id(payload["sub"])
        if not user or user.refresh_token_hash != hashlib.sha256(refresh_token.encode()).hexdigest():
            raise HTTPException(status_code=401, detail="Refresh token revoked")
        access = create_jwt({"sub": str(user.id), "org": str(user.organization_id), "role": user.role}, settings.JWT_SECRET, settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        return {"access_token": access, "token_type": "bearer", "must_change_password": bool(user.must_change_password)}

    def logout(self, user, response: Response):
        user.refresh_token_hash = None
        self.users.save(user)
        response.delete_cookie(REFRESH_COOKIE_NAME)
        self.audit.log(action="Logout", organization_id=user.organization_id, user_id=user.id)
        return {"status": "logged_out"}
