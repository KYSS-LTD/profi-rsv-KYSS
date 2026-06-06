from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.dependencies import get_db
from app.org_os.schemas import OrganizationMapResponse, ProfileContextResponse
from app.org_os.services import OrgOSService

router = APIRouter(prefix="/api/v2/org-os", tags=["Organizational Operating System"])


@router.get("/map", response_model=OrganizationMapResponse)
def organization_map(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return OrgOSService(db).organization_map(current_user)


@router.get("/profiles/{employee_id}", response_model=ProfileContextResponse)
def profile_context(employee_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return OrgOSService(db).profile_context(current_user, employee_id)
