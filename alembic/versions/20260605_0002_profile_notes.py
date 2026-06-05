"""add profile notes

Revision ID: 20260605_0002
Revises: 20260605_0001
Create Date: 2026-06-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260605_0002"
down_revision: Union[str, Sequence[str], None] = "20260605_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "profile_notes",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("task_id", sa.String(128)),
        sa.Column("meeting_id", sa.String(128)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_profile_notes_organization_id", "profile_notes", ["organization_id"])
    op.create_index("ix_profile_notes_user_id", "profile_notes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_profile_notes_user_id", table_name="profile_notes")
    op.drop_index("ix_profile_notes_organization_id", table_name="profile_notes")
    op.drop_table("profile_notes")
