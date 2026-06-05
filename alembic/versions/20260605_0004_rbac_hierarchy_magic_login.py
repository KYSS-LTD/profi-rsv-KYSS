"""rbac hierarchy and magic login

Revision ID: 20260605_0004
Revises: 20260605_0003
Create Date: 2026-06-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260605_0004"
down_revision: Union[str, Sequence[str], None] = "20260605_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "login_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("token", sa.String(128), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("token", name="uq_login_token_token"),
    )
    op.add_column("users", sa.Column("impersonated_by_user_id", uuid_type, nullable=True))
    op.create_foreign_key("fk_users_impersonated_by_user_id_users", "users", "users", ["impersonated_by_user_id"], ["id"])
    op.add_column("employees", sa.Column("manager_id", uuid_type, nullable=True))
    op.add_column("employees", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("employees", sa.Column("deactivated_at", sa.DateTime(), nullable=True))
    op.add_column("employees", sa.Column("deactivated_by", uuid_type, nullable=True))
    op.create_foreign_key("fk_employees_manager_id_employees", "employees", "employees", ["manager_id"], ["id"])
    op.create_foreign_key("fk_employees_deactivated_by_users", "employees", "users", ["deactivated_by"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_employees_deactivated_by_users", "employees", type_="foreignkey")
    op.drop_constraint("fk_employees_manager_id_employees", "employees", type_="foreignkey")
    for column in ["deactivated_by", "deactivated_at", "active", "manager_id"]:
        op.drop_column("employees", column)
    op.drop_constraint("fk_users_impersonated_by_user_id_users", "users", type_="foreignkey")
    op.drop_column("users", "impersonated_by_user_id")
    op.drop_table("login_tokens")
