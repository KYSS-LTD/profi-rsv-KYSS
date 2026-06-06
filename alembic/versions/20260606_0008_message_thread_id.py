"""store telegram message thread ids

Revision ID: 20260606_0008
Revises: 20260606_0007
Create Date: 2026-06-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260606_0008"
down_revision: Union[str, Sequence[str], None] = "20260606_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("message_thread_id", sa.Integer(), nullable=True))
    op.create_index("ix_messages_message_thread_id", "messages", ["message_thread_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_message_thread_id", table_name="messages")
    op.drop_column("messages", "message_thread_id")
