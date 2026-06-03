from pydantic import BaseModel
from typing import Any, Dict, Optional

class TaskCreate(BaseModel):
    title: str
    description: str | None = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    priority: str

    model_config = {
        "from_attributes": True
    }

class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None