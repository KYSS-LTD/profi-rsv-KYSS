from fastapi import APIRouter, Request
from app.demo_data import MEETING, copy_data

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.get("/{meeting_id}/summary")
async def get_meeting_summary(meeting_id: str):
    meeting = copy_data(MEETING)
    meeting["id"] = meeting_id or meeting["id"]
    return meeting


@router.post("/upload")
async def upload_meeting(request: Request):
    await request.body()
    return {
        "meeting_id": "meeting_1",
        "status": "transcribing",
        "filename": None,
        "team_id": "team_1",
        "title": "Встреча команды",
    }
