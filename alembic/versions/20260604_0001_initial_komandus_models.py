"""initial komandus integration models

Revision ID: 20260604_0001
Revises: 
Create Date: 2026-06-04 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260604_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=64), server_default="member", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_update_id", sa.Integer(), nullable=True),
        sa.Column("telegram_message_id", sa.Integer(), nullable=True),
        sa.Column("telegram_user_id", sa.Integer(), nullable=True),
        sa.Column("chat_id", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("voice_file_id", sa.String(length=255), nullable=True),
        sa.Column("raw_update", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("telegram_update_id", "telegram_message_id", "telegram_user_id", "chat_id"):
        op.create_index(op.f(f"ix_messages_{column}"), "messages", [column])

    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), server_default="Встреча команды", nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("decisions", json_type, server_default="[]", nullable=False),
        sa.Column("action_items", json_type, server_default="[]", nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=64), server_default="meeting_audio", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meetings_team_id"), "meetings", ["team_id"])

    op.create_table(
        "task_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("meeting_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("assignee_raw", sa.String(length=255), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_raw", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.String(length=32), server_default="medium", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("source", sa.String(length=64), server_default="telegram_text", nullable=False),
        sa.Column("missing_fields", json_type, server_default="[]", nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("raw_llm_json", json_type, nullable=True),
        sa.Column("source_excerpt", sa.Text(), nullable=True),
        sa.Column("source_message_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("team_id", "message_id", "meeting_id", "assignee_id", "status", "source"):
        op.create_index(op.f(f"ix_task_candidates_{column}"), "task_candidates", [column])
    op.create_index("ix_task_candidates_team_status", "task_candidates", ["team_id", "status"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=True),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("external_kanban_id", sa.String(length=255), nullable=True),
        sa.Column("external_kanban_url", sa.String(length=500), nullable=True),
        sa.Column("kanban_provider", sa.String(length=32), server_default="internal", nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("assignee_raw", sa.String(length=255), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="todo", nullable=False),
        sa.Column("priority", sa.String(length=32), server_default="medium", nullable=False),
        sa.Column("source", sa.String(length=64), server_default="telegram_text", nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_by_ai", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("source_message_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status_change_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status_changed_count", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["task_candidates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id"),
    )
    for column in ("team_id", "candidate_id", "external_kanban_id", "title", "assignee_id", "deadline", "status", "source"):
        op.create_index(op.f(f"ix_tasks_{column}"), "tasks", [column])
    op.create_index("ix_tasks_team_status", "tasks", ["team_id", "status"])

    op.create_table(
        "task_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("old_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), server_default="dashboard", nullable=False),
        sa.Column("changed_by", sa.String(length=255), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_status_history_task_id"), "task_status_history", ["task_id"])
    op.create_index(op.f("ix_task_status_history_source"), "task_status_history", ["source"])


def downgrade() -> None:
    op.drop_table("task_status_history")
    op.drop_index("ix_tasks_team_status", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_task_candidates_team_status", table_name="task_candidates")
    op.drop_table("task_candidates")
    op.drop_table("meetings")
    op.drop_table("messages")
    op.drop_table("users")
