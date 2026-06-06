from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


TELEGRAM_BIGINT_COLUMNS = {
    "telegram_chats": ("telegram_chat_id", "last_processed_message_id"),
    "messages": ("chat_id", "telegram_message_id", "telegram_user_id"),
    "task_candidates": ("chat_id", "source_chat_id", "source_message_id"),
    "telegram_sources": ("chat_id",),
    "employees": ("telegram_user_id",),
}

MVP_COMPAT_COLUMNS = {
    "telegram_chats": {
        "organization_id": "INTEGER REFERENCES organizations(id)",
    },
    "messages": {
        "organization_id": "INTEGER REFERENCES organizations(id)",
    },
    "task_candidates": {
        "organization_id": "INTEGER REFERENCES organizations(id)",
        "description": "TEXT",
        "assignee_id": "INTEGER REFERENCES employees(id)",
        "deadline": "TEXT",
        "source_message_id": "BIGINT",
        "source_chat_id": "BIGINT",
        "rejection_reason": "TEXT",
        "updated_at": "TIMESTAMP",
    },
    "tasks": {
        "organization_id": "INTEGER REFERENCES organizations(id)",
        "assignee_employee_id": "INTEGER REFERENCES employees(id)",
        "creator_id": "INTEGER REFERENCES employees(id)",
        "due_date": "TEXT",
        "yougile_task_id": "VARCHAR",
        "yougile_url": "TEXT",
    },
}


def ensure_telegram_bigint_columns(engine: Engine) -> None:
    """Keep existing dev/demo Postgres schemas compatible with the MVP models."""
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table_name, column_names in TELEGRAM_BIGINT_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name in column_names:
                if column_name not in existing_columns:
                    continue
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ALTER COLUMN {column_name} TYPE BIGINT "
                        f"USING {column_name}::bigint"
                    )
                )


def ensure_mvp_schema_columns(engine: Engine) -> None:
    """Add minimal MVP columns to already-created Postgres tables.

    SQLAlchemy ``create_all`` creates the new tables for a fresh installation,
    but it does not mutate older local databases. These additive, nullable
    columns keep existing data and avoid rewriting migrations.
    """
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table_name, columns in MVP_COMPAT_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in columns.items():
                if column_name in existing_columns:
                    continue
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {ddl}"))
