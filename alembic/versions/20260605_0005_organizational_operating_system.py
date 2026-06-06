"""organizational operating system

Revision ID: 20260605_0005
Revises: 20260605_0004
Create Date: 2026-06-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260605_0005"
down_revision: Union[str, Sequence[str], None] = "20260605_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table("system_roles", sa.Column("id", uuid_type, primary_key=True), sa.Column("name", sa.String(32), nullable=False), sa.Column("description", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("name", name="uq_system_role_name"))
    op.create_table("positions", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text()), sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("organization_id", "name", name="uq_position_org_name"))
    op.create_table("organizational_units", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("parent_id", uuid_type, sa.ForeignKey("organizational_units.id"), nullable=True, index=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("unit_type", sa.String(64), nullable=False, server_default="DEPARTMENT"), sa.Column("description", sa.Text()), sa.Column("lead_employee_id", uuid_type, sa.ForeignKey("employees.id"), nullable=True, index=True), sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("organization_id", "parent_id", "name", name="uq_org_unit_parent_name"))
    op.create_table("relationship_types", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("code", sa.String(64), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("organization_id", "code", name="uq_relationship_type_org_code"))

    for table in ["users", "employees"]:
        op.add_column(table, sa.Column("system_role_id", uuid_type, nullable=True))
        op.add_column(table, sa.Column("permission_scopes", sa.JSON(), nullable=True))
        op.create_foreign_key(f"fk_{table}_system_role_id_system_roles", table, "system_roles", ["system_role_id"], ["id"])
    op.add_column("users", sa.Column("first_name", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(1024), nullable=True))
    op.add_column("users", sa.Column("position_id", uuid_type, nullable=True))
    op.add_column("users", sa.Column("manager_id", uuid_type, nullable=True))
    op.add_column("users", sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"))
    op.add_column("users", sa.Column("hire_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("termination_date", sa.Date(), nullable=True))
    op.create_foreign_key("fk_users_position_id_positions", "users", "positions", ["position_id"], ["id"])
    op.create_foreign_key("fk_users_manager_id_users", "users", "users", ["manager_id"], ["id"])
    op.add_column("employees", sa.Column("organizational_unit_id", uuid_type, nullable=True))
    op.add_column("employees", sa.Column("position_id", uuid_type, nullable=True))
    op.add_column("employees", sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"))
    op.add_column("employees", sa.Column("hire_date", sa.Date(), nullable=True))
    op.add_column("employees", sa.Column("termination_date", sa.Date(), nullable=True))
    op.create_foreign_key("fk_employees_organizational_unit_id_organizational_units", "employees", "organizational_units", ["organizational_unit_id"], ["id"])
    op.create_foreign_key("fk_employees_position_id_positions", "employees", "positions", ["position_id"], ["id"])

    op.create_table("responsibility_areas", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text()), sa.Column("owner_user_id", uuid_type, sa.ForeignKey("users.id"), nullable=True, index=True), sa.Column("backup_owner_id", uuid_type, sa.ForeignKey("users.id"), nullable=True, index=True), sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("organization_id", "name", name="uq_responsibility_org_name"))
    op.create_table("delegations", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("delegator_id", uuid_type, sa.ForeignKey("users.id"), nullable=False, index=True), sa.Column("delegate_id", uuid_type, sa.ForeignKey("users.id"), nullable=False, index=True), sa.Column("scope", sa.JSON(), nullable=False), sa.Column("start_date", sa.DateTime(), nullable=False), sa.Column("end_date", sa.DateTime(), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("successors", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("subject_user_id", uuid_type, sa.ForeignKey("users.id"), nullable=True, index=True), sa.Column("position_id", uuid_type, sa.ForeignKey("positions.id"), nullable=True, index=True), sa.Column("successor_user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False, index=True), sa.Column("readiness", sa.String(32), nullable=False, server_default="PLANNED"), sa.Column("notes", sa.Text()), sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("organizational_relationships", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("relationship_type_id", uuid_type, sa.ForeignKey("relationship_types.id"), nullable=False, index=True), sa.Column("source_user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False, index=True), sa.Column("target_user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False, index=True), sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"), sa.Column("metadata_json", sa.JSON()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("approval_chains", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("steps", sa.JSON(), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("escalation_policies", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("rules", sa.JSON(), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("organizational_events", sa.Column("id", uuid_type, primary_key=True), sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id"), nullable=False, index=True), sa.Column("actor_user_id", uuid_type, sa.ForeignKey("users.id"), nullable=True, index=True), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("entity_type", sa.String(64)), sa.Column("entity_id", sa.String(64)), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("occurred_at", sa.DateTime(), nullable=False))

    op.add_column("komandus_tasks", sa.Column("assigned_position_id", uuid_type, nullable=True))
    op.add_column("komandus_tasks", sa.Column("assigned_organizational_unit_id", uuid_type, nullable=True))
    op.add_column("komandus_tasks", sa.Column("assigned_responsibility_area_id", uuid_type, nullable=True))
    op.add_column("komandus_tasks", sa.Column("current_owner_user_id", uuid_type, nullable=True))
    op.create_foreign_key("fk_tasks_assigned_position_id_positions", "komandus_tasks", "positions", ["assigned_position_id"], ["id"])
    op.create_foreign_key("fk_tasks_assigned_org_unit_id_org_units", "komandus_tasks", "organizational_units", ["assigned_organizational_unit_id"], ["id"])
    op.create_foreign_key("fk_tasks_assigned_responsibility_area_id_responsibility_areas", "komandus_tasks", "responsibility_areas", ["assigned_responsibility_area_id"], ["id"])
    op.create_foreign_key("fk_tasks_current_owner_user_id_users", "komandus_tasks", "users", ["current_owner_user_id"], ["id"])

    op.execute("UPDATE users SET role='OWNER' WHERE role IN ('SUPER_ADMIN','ORG_OWNER')")
    op.execute("UPDATE users SET role='ADMIN' WHERE role='PRODUCT_MANAGER'")
    op.execute("UPDATE users SET role='MANAGER' WHERE role IN ('DEPARTMENT_MANAGER','TEAM_LEAD')")
    op.execute("UPDATE users SET role='OBSERVER' WHERE role='VIEWER'")
    op.execute("UPDATE employees SET role='OWNER' WHERE role IN ('SUPER_ADMIN','ORG_OWNER')")
    op.execute("UPDATE employees SET role='ADMIN' WHERE role='PRODUCT_MANAGER'")
    op.execute("UPDATE employees SET role='MANAGER' WHERE role IN ('DEPARTMENT_MANAGER','TEAM_LEAD')")
    op.execute("UPDATE employees SET role='OBSERVER' WHERE role='VIEWER'")


def downgrade() -> None:
    op.execute("UPDATE users SET role='ORG_OWNER' WHERE role='OWNER'")
    op.execute("UPDATE users SET role='PRODUCT_MANAGER' WHERE role='ADMIN'")
    op.execute("UPDATE users SET role='DEPARTMENT_MANAGER' WHERE role='MANAGER'")
    op.execute("UPDATE users SET role='VIEWER' WHERE role='OBSERVER'")
    op.execute("UPDATE employees SET role='ORG_OWNER' WHERE role='OWNER'")
    op.execute("UPDATE employees SET role='PRODUCT_MANAGER' WHERE role='ADMIN'")
    op.execute("UPDATE employees SET role='DEPARTMENT_MANAGER' WHERE role='MANAGER'")
    op.execute("UPDATE employees SET role='VIEWER' WHERE role='OBSERVER'")
    for name in ["fk_tasks_current_owner_user_id_users", "fk_tasks_assigned_responsibility_area_id_responsibility_areas", "fk_tasks_assigned_org_unit_id_org_units", "fk_tasks_assigned_position_id_positions"]:
        op.drop_constraint(name, "komandus_tasks", type_="foreignkey")
    for column in ["current_owner_user_id", "assigned_responsibility_area_id", "assigned_organizational_unit_id", "assigned_position_id"]:
        op.drop_column("komandus_tasks", column)
    for table in ["organizational_events", "escalation_policies", "approval_chains", "organizational_relationships", "successors", "delegations", "responsibility_areas"]:
        op.drop_table(table)
    op.drop_constraint("fk_employees_position_id_positions", "employees", type_="foreignkey")
    op.drop_constraint("fk_employees_organizational_unit_id_organizational_units", "employees", type_="foreignkey")
    for column in ["termination_date", "hire_date", "status", "position_id", "organizational_unit_id"]:
        op.drop_column("employees", column)
    op.drop_constraint("fk_users_manager_id_users", "users", type_="foreignkey")
    op.drop_constraint("fk_users_position_id_positions", "users", type_="foreignkey")
    for column in ["termination_date", "hire_date", "status", "manager_id", "position_id", "avatar_url", "last_name", "first_name"]:
        op.drop_column("users", column)
    for table in ["employees", "users"]:
        op.drop_constraint(f"fk_{table}_system_role_id_system_roles", table, type_="foreignkey")
        op.drop_column(table, "permission_scopes")
        op.drop_column(table, "system_role_id")
    op.drop_table("relationship_types")
    op.drop_table("organizational_units")
    op.drop_table("positions")
    op.drop_table("system_roles")
