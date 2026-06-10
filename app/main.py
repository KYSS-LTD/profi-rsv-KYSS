from fastapi import FastAPI, Request
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
from app.common.logging import configure_logging
from app.monitoring.metrics import increment
from app.auth.routers import router as auth_v2_router
from app.employees.routers import router as employees_v2_router
from app.boards.routers import router as boards_v2_router
from app.tasks.routers import router as tasks_v2_router
from app.analytics.routers import router as analytics_v2_router
from app.monitoring.routers import router as monitoring_router
from app.setup.routers import router as setup_v2_router
from app.organization_units.routers import router as org_units_router
from app.org_os.routers import router as org_os_router
from app.core.database import Base, engine
from app.core.schema import ensure_telegram_bigint_columns
from app.models import models as _models  # noqa: F401

configure_logging()

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

api_v2_routers = (auth_v2_router, setup_v2_router, org_units_router, employees_v2_router, boards_v2_router, tasks_v2_router, analytics_v2_router, monitoring_router, org_os_router)

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

for router in api_v2_routers:
    app.include_router(router)

for router in api_routers:
    app.include_router(router)


@app.middleware("http")
async def request_metrics_middleware(request: Request, call_next):
    increment("requests_total")
    response = await call_next(request)
    return response


@app.on_event("startup")
def create_database_tables() -> None:
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
        ensure_telegram_bigint_columns(engine)
