from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


TELEGRAM_BIGINT_COLUMNS = {
    "telegram_chats": ("telegram_chat_id", "last_processed_message_id"),
    "messages": ("chat_id", "telegram_message_id", "telegram_user_id"),
    "task_candidates": ("chat_id",),
}


def ensure_telegram_bigint_columns(engine: Engine) -> None:
    """Make Telegram identifiers signed BIGINT columns in existing Postgres DBs.

    Telegram group/supergroup chat IDs are often negative and can be larger than
    a 32-bit integer, for example ``-1001234567890``. ``create_all`` applies the
    model type for new databases, but it does not alter already-created tables,
    so dev/demo databases from an older schema need a small compatibility step.
    """
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table_name, column_names in TELEGRAM_BIGINT_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            for column_name in column_names:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ALTER COLUMN {column_name} TYPE BIGINT "
                        f"USING {column_name}::bigint"
                    )
                )
