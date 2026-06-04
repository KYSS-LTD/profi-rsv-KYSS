from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Komandus"
    APP_ENV: str = "development"
    DEBUG: bool = True

    POSTGRES_DB: str = "komandus"
    POSTGRES_USER: str = "komandus"
    POSTGRES_PASSWORD: str = "komandus"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    BOT_TOKEN: str = ""
    OPENAI_API_KEY: str = ""

    KANBAN_PROVIDER: str = "internal"
    YOUGILE_API_URL: str = "https://yougile.com/api-v2"
    YOUGILE_API_KEY: str = ""
    YOUGILE_COLUMN_ID: str = ""
    TRELLO_API_URL: str = "https://api.trello.com/1"
    TRELLO_API_KEY: str = ""
    TRELLO_TOKEN: str = ""
    TRELLO_LIST_ID: str = ""

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
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
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
