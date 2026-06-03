from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.api.telegram import router as telegram_router
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Komandus API",
)

app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(telegram_router)