from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import ChangePasswordRequest, LoginRequest, MagicLoginRequest, MeResponse, TokenResponse
from app.auth.services import AuthService, REFRESH_COOKIE_NAME
from app.dependencies import get_db

router = APIRouter(prefix="/api/v2/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, summary="Login", description="Issue a 15-minute access JWT and a 7-day HttpOnly refresh cookie.", responses={200: {"description": "Authenticated"}})
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    return AuthService(db).login(payload.email, payload.password, response)


@router.post("/magic-login", response_model=TokenResponse, summary="Magic login", description="Consume a one-time Telegram magic login token and authenticate the user.")
def magic_login(payload: MagicLoginRequest, response: Response, db: Session = Depends(get_db)):
    return AuthService(db).magic_login(payload.token, response)


@router.post("/change-password", summary="Change password", description="Set a new password after first magic-login.")
def change_password(payload: ChangePasswordRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return AuthService(db).change_password(current_user, payload.new_password)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token", description="Rotate a short-lived access token using the HttpOnly refresh cookie.")
def refresh(response: Response, refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME), db: Session = Depends(get_db)):
    return AuthService(db).refresh(refresh_token, response)


@router.post("/logout", summary="Logout", description="Revoke the refresh token and clear the HttpOnly cookie.")
def logout(response: Response, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return AuthService(db).logout(current_user, response)


@router.get("/me", response_model=MeResponse, summary="Current user", description="Return authenticated user profile and tenant context.")
def me(current_user=Depends(get_current_user)):
    return current_user
