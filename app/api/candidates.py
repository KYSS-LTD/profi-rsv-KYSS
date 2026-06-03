from fastapi import APIRouter, Body, HTTPException
from app.demo_data import TASK_CANDIDATES, copy_data

router = APIRouter(prefix="/task-candidates", tags=["Task candidates"])


@router.get("")
async def get_candidates(status: str | None = None):
    candidates = TASK_CANDIDATES
    if status:
        candidates = [candidate for candidate in candidates if candidate.get("status") == status]
    return copy_data(candidates)


@router.post("/{candidate_id}/reject")
async def reject_candidate(candidate_id: str, payload: dict = Body(default_factory=dict)):
    candidate = next((item for item in TASK_CANDIDATES if item["id"] == candidate_id), None)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate["status"] = "rejected"
    candidate["reason"] = payload.get("reason") or "other"
    return {"status": "rejected", "candidate_id": candidate_id}
