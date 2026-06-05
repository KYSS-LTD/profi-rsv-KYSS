from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.setup.schemas import SetupRequest, SetupStatusResponse, SetupTokenResponse
from app.setup.services import SetupService

router = APIRouter(prefix="/api/v2/setup", tags=["Setup"])


@router.get(
    "/status",
    response_model=SetupStatusResponse,
    summary="Check system initialization status",
    description="Returns whether Komandus has at least one user and therefore has already completed primary setup.",
    responses={
        200: {
            "description": "System initialization status",
            "content": {"application/json": {"examples": {"initialized": {"value": {"initialized": True}}, "not_initialized": {"value": {"initialized": False}}}}},
        }
    },
)
def setup_status(db: Session = Depends(get_db)):
    return SetupStatusResponse(initialized=SetupService(db).is_initialized())


@router.post(
    "",
    response_model=SetupTokenResponse,
    summary="Initialize system",
    description="Creates the first organization and first active MANAGER user. This endpoint is available only while the users table is empty and returns the same token response as login.",
    responses={
        200: {
            "description": "System initialized and authenticated",
            "content": {"application/json": {"example": {"access_token": "eyJ...", "token_type": "bearer"}}},
        },
        403: {"description": "System already initialized", "content": {"application/json": {"example": {"detail": "System already initialized"}}}},
    },
)
def setup(payload: SetupRequest, response: Response, db: Session = Depends(get_db)):
    return SetupService(db).initialize(payload, response)
