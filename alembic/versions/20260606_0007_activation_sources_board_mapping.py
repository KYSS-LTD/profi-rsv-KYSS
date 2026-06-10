"""activation tokens, full source mappings, and board mappings

Revision ID: 20260606_0007
Revises: 20260606_0006
Create Date: 2026-06-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260606_0007"
down_revision: Union[str, Sequence[str], None] = "20260606_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "activation_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("token", sa.String(128), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("token", name="uq_activation_token_token"),
    )
    op.add_column("task_sources", sa.Column("yougile_board_id", sa.String(255), nullable=True))
    op.add_column("task_sources", sa.Column("yougile_column_id", sa.String(255), nullable=True))
    op.add_column("task_sources", sa.Column("responsibility_area_id", uuid_type, nullable=True))
    op.alter_column("task_sources", "telegram_chat_id", existing_type=sa.BigInteger(), nullable=True)
    op.create_index("ix_task_sources_yougile_board_id", "task_sources", ["yougile_board_id"])
    op.create_index("ix_task_sources_yougile_column_id", "task_sources", ["yougile_column_id"])
    op.create_foreign_key("fk_task_sources_responsibility_area_id", "task_sources", "responsibility_areas", ["responsibility_area_id"], ["id"])
    op.create_table(
        "board_mappings",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("provider", sa.String(32), nullable=False, server_default="yougile"),
        sa.Column("department_id", uuid_type, sa.ForeignKey("departments.id"), nullable=True, index=True),
        sa.Column("team_id", uuid_type, sa.ForeignKey("teams.id"), nullable=True, index=True),
        sa.Column("board_integration_id", uuid_type, sa.ForeignKey("board_integrations.id"), nullable=True, index=True),
        sa.Column("external_project_id", sa.String(255), nullable=True),
        sa.Column("external_board_id", sa.String(255), nullable=False, index=True),
        sa.Column("external_board_name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "provider", "external_board_id", name="uq_board_mapping_external_board"),
    )


def downgrade() -> None:
    op.drop_table("board_mappings")
    op.drop_constraint("fk_task_sources_responsibility_area_id", "task_sources", type_="foreignkey")
    op.drop_index("ix_task_sources_yougile_column_id", table_name="task_sources")
    op.drop_index("ix_task_sources_yougile_board_id", table_name="task_sources")
    op.alter_column("task_sources", "telegram_chat_id", existing_type=sa.BigInteger(), nullable=False)
    op.drop_column("task_sources", "responsibility_area_id")
    op.drop_column("task_sources", "yougile_column_id")
    op.drop_column("task_sources", "yougile_board_id")
    op.drop_table("activation_tokens")
