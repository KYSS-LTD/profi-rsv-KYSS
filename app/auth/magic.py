from __future__ import annotations

from datetime import datetime, timedelta
import secrets

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import LoginToken, User

MAGIC_LOGIN_TTL_HOURS = 24


class MagicLoginService:
    def __init__(self, db: Session):
        self.db = db

    def create_token(self, user_id, *, ttl_hours: int = MAGIC_LOGIN_TTL_HOURS) -> LoginToken:
        token = secrets.token_urlsafe(48)[:128]
        row = LoginToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
            used=False,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def build_magic_login_url(self, token: str) -> str | None:
        return self.build_activation_url(token)

    def build_activation_url(self, token: str) -> str | None:
        public_url = settings.public_app_url
        if not public_url:
            return None
        return f"{public_url}/activate?token={token}"

    def consume_token(self, token: str) -> User | None:
        row = self.db.query(LoginToken).filter(LoginToken.token == token).first()
        if not row or row.used or row.expires_at <= datetime.utcnow():
            return None
        user = self.db.query(User).filter(User.id == row.user_id, User.is_active.is_(True)).first()
        if not user:
            return None
        row.used = True
        user.must_change_password = True
        self.db.commit()
        self.db.refresh(user)
        return user
