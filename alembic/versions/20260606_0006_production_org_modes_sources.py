"""production org modes and task sources

Revision ID: 20260606_0006
Revises: 20260605_0005
Create Date: 2026-06-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260606_0006"
down_revision: Union[str, Sequence[str], None] = "20260605_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column("organizations", sa.Column("org_mode", sa.String(32), nullable=False, server_default="SIMPLE"))
    op.add_column("organizations", sa.Column("hierarchy_setup_state", sa.JSON(), nullable=True))
    op.add_column("organization_chats", sa.Column("team_id", uuid_type, nullable=True))
    op.create_foreign_key("fk_organization_chats_team_id_teams", "organization_chats", "teams", ["team_id"], ["id"])
    op.add_column("telegram_connect_codes", sa.Column("team_id", uuid_type, nullable=True))
    op.create_foreign_key("fk_telegram_connect_codes_team_id_teams", "telegram_connect_codes", "teams", ["team_id"], ["id"])
    op.add_column("board_integrations", sa.Column("department_id", uuid_type, nullable=True))
    op.add_column("board_integrations", sa.Column("team_id", uuid_type, nullable=True))
    op.create_foreign_key("fk_board_integrations_department_id_departments", "board_integrations", "departments", ["department_id"], ["id"])
    op.create_foreign_key("fk_board_integrations_team_id_teams", "board_integrations", "teams", ["team_id"], ["id"])
    op.create_table(
        "task_sources",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("telegram_topic_id", sa.Integer(), nullable=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department_id", uuid_type, sa.ForeignKey("departments.id"), nullable=True, index=True),
        sa.Column("team_id", uuid_type, sa.ForeignKey("teams.id"), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ai_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "source_type", "telegram_chat_id", "telegram_topic_id", name="uq_task_source_telegram"),
    )


def downgrade() -> None:
    op.drop_table("task_sources")
    op.drop_constraint("fk_board_integrations_team_id_teams", "board_integrations", type_="foreignkey")
    op.drop_constraint("fk_board_integrations_department_id_departments", "board_integrations", type_="foreignkey")
    op.drop_column("board_integrations", "team_id")
    op.drop_column("board_integrations", "department_id")
    op.drop_constraint("fk_telegram_connect_codes_team_id_teams", "telegram_connect_codes", type_="foreignkey")
    op.drop_column("telegram_connect_codes", "team_id")
    op.drop_constraint("fk_organization_chats_team_id_teams", "organization_chats", type_="foreignkey")
    op.drop_column("organization_chats", "team_id")
    op.drop_column("organizations", "hierarchy_setup_state")
    op.drop_column("organizations", "org_mode")
