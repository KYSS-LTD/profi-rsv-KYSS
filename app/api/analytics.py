from fastapi import APIRouter
from app.demo_data import TASKS

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/team")
async def get_team_analytics():
    done_tasks = len([task for task in TASKS if task.get("status") == "done"])
    return {
        "ai_created_tasks": len([task for task in TASKS if task.get("created_by_ai")]),
        "auto_confirmed": 8,
        "waiting_confirmation": 3,
        "rejected_suggestions": 1,
        "voice_messages_processed": 4,
        "meetings_summarized": 1,
        "average_confidence": 0.87,
        "overdue_tasks": 2,
        "done_tasks": done_tasks,
        "team_velocity": {"done_this_week": 18, "avg_lead_time_hours": 14.5, "overdue_percent": 12},
        "ai_quality": {"average_confidence": 0.87, "auto_created": 8, "rejected_suggestions": 1},
    }


@router.get("/leaderboard")
async def get_leaderboard():
    return [
        {"user_id": "user_ivan", "name": "Иван", "xp": 420, "level": "Team Driver", "done_tasks": 5},
        {"user_id": "user_pavel", "name": "Павел", "xp": 360, "level": "Reliable Executor", "done_tasks": 4},
        {"user_id": "user_daniil", "name": "Даниил", "xp": 330, "level": "Contributor", "done_tasks": 3},
    ]
