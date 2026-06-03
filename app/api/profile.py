from fastapi import APIRouter, Body, HTTPException
from app.demo_data import ACHIEVEMENTS, NOTES, PROFILE, RECOMMENDATIONS, TASKS, copy_data, now_iso

router = APIRouter(tags=["Profile"])


@router.get("/profile/me")
async def get_profile():
    return copy_data(PROFILE)


@router.get("/users/{user_id}/digest")
async def get_user_digest(user_id: str):
    user_tasks = [task for task in TASKS if task.get("assignee_id") == user_id]
    return {
        "user_id": user_id,
        "date": "2026-06-03",
        "tasks_today": copy_data(user_tasks),
        "overdue_tasks": [],
        "upcoming_deadlines": copy_data([task for task in TASKS if task.get("status") != "done"][:3]),
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
