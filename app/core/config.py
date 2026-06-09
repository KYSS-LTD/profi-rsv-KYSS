from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


@dataclass(frozen=True)
class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Komandus")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = _get_bool("DEBUG", True)

    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "komandus")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "komandus")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "komandus")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = _get_int("POSTGRES_PORT", 5432)

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
    ACCESS_TOKEN_EXPIRE_SECONDS: int = _get_int("ACCESS_TOKEN_EXPIRE_SECONDS", 900)
    REFRESH_TOKEN_EXPIRE_SECONDS: int = _get_int("REFRESH_TOKEN_EXPIRE_SECONDS", 604800)
    YOUGILE_API_BASE_URL: str = os.getenv("YOUGILE_API_BASE_URL", "https://ru.yougile.com/api-v2")
    APP_PUBLIC_URL: str | None = os.getenv("APP_PUBLIC_URL")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    TELEGRAM_BOT_USERNAME: str | None = os.getenv("TELEGRAM_BOT_USERNAME")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/2")

    LLM_ENGINE_ENABLED: bool = _get_bool("LLM_ENGINE_ENABLED", False)
    LLM_PROCESSING_ENABLED: bool = _get_bool("LLM_PROCESSING_ENABLED", False)
    LLM_PROCESSING_PATH: str = os.getenv("LLM_PROCESSING_PATH", "LLMProcessing")
    TELEGRAM_CONTEXT_LIMIT: int = _get_int("TELEGRAM_CONTEXT_LIMIT", 80)
    AUTO_CREATE_TABLES: bool = _get_bool("AUTO_CREATE_TABLES", True)

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def public_app_url(self) -> str | None:
        value = (self.APP_PUBLIC_URL or "").strip().rstrip("/")
        return value or None

    @property
    def telegram_bot_url(self) -> str | None:
        username = (self.TELEGRAM_BOT_USERNAME or "").strip().lstrip("@")
        return f"https://t.me/{username}" if username else None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
