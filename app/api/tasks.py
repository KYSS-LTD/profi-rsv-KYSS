from fastapi import APIRouter, Body, HTTPException, Query
from app.demo_data import TASKS, TASK_CANDIDATES, copy_data, now_iso
from app.schemas import TaskCreate

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


def _find_task(task_id: str) -> dict:
    task = next((item for item in TASKS if str(item["id"]) == str(task_id)), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("")
async def get_tasks(
    team_id: str | None = None,
    assignee_id: str | None = None,
    status: str | None = None,
    source: str | None = None,
):
    tasks = TASKS
    if team_id:
        tasks = [task for task in tasks if task.get("team_id") == team_id]
    if assignee_id:
        tasks = [task for task in tasks if task.get("assignee_id") == assignee_id]
    if status:
        tasks = [task for task in tasks if task.get("status") == status]
    if source:
        tasks = [task for task in tasks if task.get("source") == source]
    return copy_data(tasks)


@router.post("", status_code=201)
async def create_task(payload: TaskCreate):
    task = {
        "id": f"task_{len(TASKS) + 1}",
        "team_id": "team_1",
        "title": payload.title,
        "description": payload.description,
        "assignee": None,
        "assignee_id": None,
        "deadline": None,
        "status": "todo",
        "priority": "medium",
        "source": "telegram_text",
        "confidence": None,
        "created_by_ai": False,
        "kanban_provider": "internal",
        "status_changed_count": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    TASKS.append(task)
    return copy_data(task)


@router.get("/my")
async def get_my_tasks(user_id: str = Query(default="user_ivan")):
    return copy_data([task for task in TASKS if task.get("assignee_id") == user_id])


@router.patch("/{task_id}/status")
async def update_task_status(task_id: str, payload: dict = Body(default_factory=dict)):
    task = _find_task(task_id)
    old_status = task["status"]
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=422, detail="status is required")

    task["status"] = new_status
    task["updated_at"] = now_iso()
    task["last_status_change_at"] = task["updated_at"]
    task["status_changed_count"] = int(task.get("status_changed_count") or 0) + 1
    if new_status == "done":
        task["closed_at"] = task["updated_at"]

    return {
        "task_id": task_id,
        "old_status": old_status,
        "new_status": new_status,
        "external_synced": task.get("kanban_provider") == "external",
        "updated_at": task["updated_at"],
    }


@router.post("/{task_id}/reschedule")
async def reschedule_task(task_id: str, payload: dict = Body(default_factory=dict)):
    task = _find_task(task_id)
    new_deadline = payload.get("new_deadline")
    if not new_deadline:
        raise HTTPException(status_code=422, detail="new_deadline is required")

    task["deadline"] = new_deadline
    task["updated_at"] = now_iso()
    return {"task_id": task_id, "deadline": new_deadline, "reminders_rebuilt": True}


@router.post("/candidates/{candidate_id}/confirm")
async def confirm_candidate(candidate_id: str, payload: dict = Body(default_factory=dict)):
    candidate = next((item for item in TASK_CANDIDATES if item["id"] == candidate_id), None)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    overrides = payload.get("overrides") or {}
    candidate["status"] = "confirmed"
    task = {
        "id": f"task_from_{candidate_id}",
        "team_id": candidate.get("team_id", "team_1"),
        "candidate_id": candidate_id,
        "title": overrides.get("title") or candidate["title"],
        "description": overrides.get("description") or candidate.get("description"),
        "assignee": overrides.get("assignee_raw") or candidate.get("assignee_raw"),
        "assignee_id": overrides.get("assignee_id") or candidate.get("assignee_id"),
        "deadline": overrides.get("deadline") or candidate.get("deadline"),
        "status": "todo",
        "priority": overrides.get("priority") or candidate.get("priority", "medium"),
        "source": candidate.get("source", "telegram_text"),
        "confidence": candidate.get("confidence"),
        "created_by_ai": True,
        "kanban_provider": "internal",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    TASKS.append(task)
    return {"task_id": task["id"], "external_kanban_id": None, "external_kanban_url": None, "status": "created"}


@router.post("/candidates/{candidate_id}/reject")
async def reject_candidate_from_tasks(candidate_id: str, payload: dict = Body(default_factory=dict)):
    candidate = next((item for item in TASK_CANDIDATES if item["id"] == candidate_id), None)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate["status"] = "rejected"
    candidate["reason"] = payload.get("reason") or "other"
    return {"status": "rejected", "candidate_id": candidate_id}
