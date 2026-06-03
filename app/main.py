from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router
from app.api.candidates import router as candidates_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.meetings import router as meetings_router
from app.api.profile import router as profile_router
from app.api.tasks import router as tasks_router
from app.api.telegram import router as telegram_router
from app.core.config import settings

app = FastAPI(
    title="Komandus API",
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_routers = (
    health_router,
    tasks_router,
    candidates_router,
    analytics_router,
    meetings_router,
    knowledge_router,
    profile_router,
    telegram_router,
)

for router in api_routers:
    app.include_router(router, prefix="/api")

for router in api_routers:
    app.include_router(router)
