from __future__ import annotations

import hashlib
from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session

from app.audit.services import AuditService
from app.auth.repositories import UserRepository
from app.common.security import create_jwt, verify_password
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

    def issue_tokens_for_user(self, user, response: Response, *, audit_action: str = "Login"):
        access = create_jwt({"sub": str(user.id), "org": str(user.organization_id), "role": user.role}, settings.JWT_SECRET, settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh = create_jwt({"sub": str(user.id), "typ": "refresh"}, settings.JWT_SECRET, settings.REFRESH_TOKEN_EXPIRE_SECONDS)
        user.refresh_token_hash = hashlib.sha256(refresh.encode()).hexdigest()
        self.users.save(user)
        response.set_cookie(REFRESH_COOKIE_NAME, refresh, max_age=settings.REFRESH_TOKEN_EXPIRE_SECONDS, httponly=True, secure=settings.APP_ENV == "production", samesite="lax")
        self.audit.log(action=audit_action, organization_id=user.organization_id, user_id=user.id)
        return {"access_token": access, "token_type": "bearer"}

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
        return self.login(user.email, "__already_verified__", response) if False else {"access_token": create_jwt({"sub": str(user.id), "org": str(user.organization_id), "role": user.role}, settings.JWT_SECRET, settings.ACCESS_TOKEN_EXPIRE_SECONDS), "token_type": "bearer"}

    def logout(self, user, response: Response):
        user.refresh_token_hash = None
        self.users.save(user)
        response.delete_cookie(REFRESH_COOKIE_NAME)
        self.audit.log(action="Logout", organization_id=user.organization_id, user_id=user.id)
        return {"status": "logged_out"}
