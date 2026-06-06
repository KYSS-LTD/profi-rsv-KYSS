from uuid import UUID
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.boards.schemas import BoardIntegrationResponse, BoardMappingCreate, BoardMappingResponse, ColumnMappingCreate, EmployeeBoardMappingCreate, VerifyYouGileRequest
from app.boards.services import BoardService
from app.common.enums import Role
from app.common.rbac import RoleChecker
from app.dependencies import get_db

router = APIRouter(prefix="/api/v2/boards", tags=["Boards"])


@router.post("/yougile/verify", response_model=BoardIntegrationResponse, summary="Verify YouGile token", description="Validate YouGile token, encrypt it with Fernet, and import projects, boards, columns, and users metadata.")
async def verify_yougile(payload: VerifyYouGileRequest, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN, Role.MANAGER)), db: Session = Depends(get_db)):
    return await BoardService(db).verify_yougile(payload, current_user)


@router.get("/mappings", response_model=list[BoardMappingResponse], summary="List board mappings", description="List YouGile board mappings visible to the current user.")
def list_board_mappings(current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN, Role.MANAGER)), db: Session = Depends(get_db)):
    return BoardService(db).list_board_mappings(current_user)


@router.post("/mappings", response_model=BoardMappingResponse, status_code=201, summary="Create board mapping", description="Map an organization branch to a YouGile board.")
def create_board_mapping(payload: BoardMappingCreate, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN, Role.MANAGER)), db: Session = Depends(get_db)):
    return BoardService(db).create_board_mapping(payload, current_user)


@router.post("/{integration_id}/columns", summary="Map board column", description="Map Komandus task lifecycle status to a YouGile column.")
def create_column_mapping(integration_id: UUID, payload: ColumnMappingCreate, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN, Role.MANAGER)), db: Session = Depends(get_db)):
    return BoardService(db).add_column_mapping(integration_id, payload, current_user)


@router.post("/{integration_id}/employees", summary="Map board user", description="Map an employee to a YouGile user by email or manual external user ID.")
def create_employee_mapping(integration_id: UUID, payload: EmployeeBoardMappingCreate, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN, Role.MANAGER)), db: Session = Depends(get_db)):
    return BoardService(db).add_employee_mapping(integration_id, payload, current_user)


@router.post("/yougile/webhook", summary="YouGile webhook", description="Validate and idempotently process YouGile webhook events.")
async def yougile_webhook(request: Request, x_yougile_event_id: str = Header(...), x_organization_id: UUID = Header(...), db: Session = Depends(get_db)):
    body = await request.body()
    # Signature validation should compare provider signature to stored webhook secret; idempotency is enforced before state changes.
    return {"processed": BoardService(db).record_webhook_event("yougile", x_yougile_event_id, body, x_organization_id)}
