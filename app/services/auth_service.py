from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def create_token(subject: str, organization_id: int, role: str, token_type: str = "access") -> str:
    now = datetime.now(timezone.utc)
    if token_type == "refresh":
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "org": organization_id,
        "role": role,
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    signing_input = f"{_b64encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64encode(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Invalid token format") from exc

    signing_input = f"{header_b64}.{payload_b64}"
    expected_signature = _b64encode(hmac.new(settings.JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature_b64, expected_signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64decode(payload_b64))
    if payload.get("typ") != expected_type:
        raise ValueError("Invalid token type")
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Token expired")
    return payload
