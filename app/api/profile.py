from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.tasks import serialize_db_task
from app.demo_data import ACHIEVEMENTS, NOTES, PROFILE, RECOMMENDATIONS, copy_data, now_iso
from app.dependencies import get_db
from app.models.models import Task

router = APIRouter(tags=["Profile"])


@router.get("/profile/me")
async def get_profile():
    return copy_data(PROFILE)


@router.get("/users/{user_id}/digest")
async def get_user_digest(user_id: str, db: Session = Depends(get_db)):
    user_tasks = [serialize_db_task(task) for task in db.query(Task).filter(Task.assignee_id == user_id).all()]
    if not user_tasks:
        user_tasks = [serialize_db_task(task) for task in db.query(Task).filter(Task.assignee == PROFILE["name"]).all()]
    upcoming = [serialize_db_task(task) for task in db.query(Task).filter(Task.status != "done").order_by(Task.created_at.desc()).limit(3).all()]
    return {
        "user_id": user_id,
        "date": now_iso()[:10],
        "tasks_today": user_tasks,
        "overdue_tasks": [],
        "upcoming_deadlines": upcoming,
    }


@router.get("/notes/my")
async def get_notes():
    return copy_data(NOTES)


@router.post("/notes", status_code=201)
async def create_note(payload: dict = Body(default_factory=dict)):
    note = {"id": f"note_{len(NOTES) + 1}", "user_id": PROFILE["id"], "created_at": now_iso(), **payload}
    NOTES.append(note)
    return copy_data(note)


@router.patch("/notes/{note_id}")
async def update_note(note_id: str, payload: dict = Body(default_factory=dict)):
    note = next((item for item in NOTES if item["id"] == note_id), None)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note.update(payload)
    note["updated_at"] = now_iso()
    return copy_data(note)


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    global NOTES
    NOTES = [note for note in NOTES if note["id"] != note_id]
    return {"status": "deleted", "note_id": note_id}


@router.get("/users/{user_id}/achievements")
async def get_achievements(user_id: str):
    return copy_data(ACHIEVEMENTS)


@router.get("/users/{user_id}/recommendations")
async def get_recommendations(user_id: str):
    return copy_data(RECOMMENDATIONS)
