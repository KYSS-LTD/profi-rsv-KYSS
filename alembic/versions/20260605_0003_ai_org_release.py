"""ai organization release

Revision ID: 20260605_0003
Revises: 20260605_0002
Create Date: 2026-06-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260605_0003"
down_revision: Union[str, Sequence[str], None] = "20260605_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

uuid_type = postgresql.UUID(as_uuid=True)

def upgrade() -> None:
    op.create_table("departments", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("organization_id", "name", name="uq_department_org_name"))
    op.create_table("teams", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False), sa.Column("department_id", uuid_type, sa.ForeignKey("departments.id"), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("department_id", "name", name="uq_team_department_name"))
    op.create_table("organization_chats", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False), sa.Column("department_id", uuid_type, sa.ForeignKey("departments.id")), sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("chat_type", sa.String(64)), sa.Column("members_count", sa.Integer()), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("ai_enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("bot_is_admin", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("connected_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("organization_id", "telegram_chat_id", name="uq_org_chat_telegram_id"))
    op.create_table("telegram_connect_codes", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False), sa.Column("department_id", uuid_type, sa.ForeignKey("departments.id")), sa.Column("code", sa.String(16), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("expires_at", sa.DateTime()), sa.Column("used_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("code", name="uq_telegram_connect_code"))
    op.create_table("notifications", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False), sa.Column("user_id", uuid_type, sa.ForeignKey("users.id")), sa.Column("employee_id", uuid_type, sa.ForeignKey("employees.id")), sa.Column("type", sa.String(64), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("body", sa.Text()), sa.Column("entity_type", sa.String(64)), sa.Column("entity_id", sa.String(64)), sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.add_column("users", sa.Column("department_id", uuid_type, sa.ForeignKey("departments.id")))
    op.add_column("users", sa.Column("team_id", uuid_type, sa.ForeignKey("teams.id")))
    op.add_column("users", sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()))
    for column in ["department_id", "team_id"]:
        op.add_column("employees", sa.Column(column, uuid_type))
    op.create_foreign_key("fk_employees_department_id_departments", "employees", "departments", ["department_id"], ["id"])
    op.create_foreign_key("fk_employees_team_id_teams", "employees", "teams", ["team_id"], ["id"])
    for name, type_ in [("position", sa.String(255)), ("telegram_username", sa.String(255)), ("telegram_first_name", sa.String(255)), ("telegram_last_name", sa.String(255)), ("avatar_url", sa.String(1024)), ("telegram_status", sa.String(32)), ("telegram_connected_at", sa.DateTime()), ("generated_password", sa.String(128))]:
        op.add_column("employees", sa.Column(name, type_, nullable=False if name == "telegram_status" else True, server_default="PENDING" if name == "telegram_status" else None))
    for name in ["department_id", "team_id", "organization_chat_id"]:
        op.add_column("komandus_tasks", sa.Column(name, uuid_type))
    op.create_foreign_key("fk_tasks_department_id_departments", "komandus_tasks", "departments", ["department_id"], ["id"])
    op.create_foreign_key("fk_tasks_team_id_teams", "komandus_tasks", "teams", ["team_id"], ["id"])
    op.create_foreign_key("fk_tasks_organization_chat_id_chats", "komandus_tasks", "organization_chats", ["organization_chat_id"], ["id"])
    op.add_column("komandus_tasks", sa.Column("ai_summary", sa.Text()))
    op.add_column("komandus_tasks", sa.Column("source_excerpt", sa.Text()))

def downgrade() -> None:
    for column in ["source_excerpt", "ai_summary", "organization_chat_id", "team_id", "department_id"]:
        op.drop_column("komandus_tasks", column)
    for column in ["generated_password", "telegram_connected_at", "telegram_status", "avatar_url", "telegram_last_name", "telegram_first_name", "telegram_username", "position", "team_id", "department_id"]:
        op.drop_column("employees", column)
    for column in ["must_change_password", "team_id", "department_id"]:
        op.drop_column("users", column)
    op.drop_table("notifications")
    op.drop_table("telegram_connect_codes")
    op.drop_table("organization_chats")
    op.drop_table("teams")
    op.drop_table("departments")
