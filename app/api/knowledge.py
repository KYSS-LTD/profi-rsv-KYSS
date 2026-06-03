from fastapi import APIRouter, Query
from app.demo_data import KNOWLEDGE, copy_data

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("")
async def get_knowledge(limit: int | None = Query(default=None, ge=1)):
    items = KNOWLEDGE[:limit] if limit else KNOWLEDGE
    return copy_data(items)
