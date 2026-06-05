from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


# Telegram chat/user/message IDs are signed 64-bit values. Group and
# supergroup chat IDs are negative (often prefixed with -100) and do not
# fit into a 32-bit integer.
TELEGRAM_ID_TYPE = BigInteger


class TelegramChat(Base):
    __tablename__ = "telegram_chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, unique=True, index=True)
    title: Mapped[str | None]
    type: Mapped[str | None]
    last_processed_message_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_message_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, index=True)
    telegram_user_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, index=True)
    sender_name: Mapped[str | None]
    username: Mapped[str | None]
    text: Mapped[str]
    source: Mapped[str] = mapped_column(default="telegram_text")
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class TaskCandidate(Base):
    __tablename__ = "task_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, index=True)
    title: Mapped[str]
    assignee_raw: Mapped[str | None]
    deadline_raw: Mapped[str | None]
    confidence: Mapped[float]
    status: Mapped[str] = mapped_column(default="pending")
    action: Mapped[str] = mapped_column(default="create")
    source_excerpt: Mapped[str | None]
    llm_block: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("task_candidates.id"))
    title: Mapped[str]
    description: Mapped[str | None]
    assignee_id: Mapped[str | None]
    assignee: Mapped[str | None]
    deadline: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="todo")
    priority: Mapped[str] = mapped_column(default="medium")
    source: Mapped[str] = mapped_column(default="telegram_text")
    created_by_ai: Mapped[bool] = mapped_column(default=False)
    confidence: Mapped[float | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

# --- Komandus v2 SaaS models ---
import uuid
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


def uuid_pk():
    return mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def uuid_fk(target: str, *, nullable: bool = False):
    return mapped_column(PG_UUID(as_uuid=True), ForeignKey(target), nullable=nullable, index=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)




class Department(Base, TimestampMixin):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_department_org_name"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Team(Base, TimestampMixin):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("department_id", "name", name="uq_team_department_name"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    department_id: Mapped[uuid.UUID] = uuid_fk("departments.id")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="EMPLOYEE", nullable=False)
    department_id: Mapped[uuid.UUID | None] = uuid_fk("departments.id", nullable=True)
    team_id: Mapped[uuid.UUID | None] = uuid_fk("teams.id", nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(128))


class LoginToken(Base):
    __tablename__ = "login_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_login_token_token"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = uuid_fk("users.id")
    token: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    user_id: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    role: Mapped[str] = mapped_column(String(32), default="EMPLOYEE", nullable=False)
    department_id: Mapped[uuid.UUID | None] = uuid_fk("departments.id", nullable=True)
    team_id: Mapped[uuid.UUID | None] = uuid_fk("teams.id", nullable=True)
    position: Mapped[str | None] = mapped_column(String(255))
    telegram_username: Mapped[str | None] = mapped_column(String(255), index=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(255))
    telegram_last_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    telegram_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    telegram_connected_at: Mapped[datetime | None] = mapped_column(DateTime)
    generated_password: Mapped[str | None] = mapped_column(String(128))
    telegram_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TelegramAccountLink(Base, TimestampMixin):
    __tablename__ = "telegram_account_links"
    __table_args__ = (UniqueConstraint("organization_id", "telegram_id", name="uq_org_telegram_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    employee_id: Mapped[uuid.UUID] = uuid_fk("employees.id")
    telegram_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)




class OrganizationChat(Base):
    __tablename__ = "organization_chats"
    __table_args__ = (UniqueConstraint("organization_id", "telegram_chat_id", name="uq_org_chat_telegram_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    department_id: Mapped[uuid.UUID | None] = uuid_fk("departments.id", nullable=True)
    telegram_chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chat_type: Mapped[str | None] = mapped_column(String(64))
    members_count: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bot_is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TelegramConnectCode(Base):
    __tablename__ = "telegram_connect_codes"
    __table_args__ = (UniqueConstraint("code", name="uq_telegram_connect_code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    department_id: Mapped[uuid.UUID | None] = uuid_fk("departments.id", nullable=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class BoardIntegration(Base, TimestampMixin):
    __tablename__ = "board_integrations"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    provider: Mapped[str] = mapped_column(String(32), default="yougile", nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_api_token: Mapped[str] = mapped_column(Text, nullable=False)
    external_project_id: Mapped[str | None] = mapped_column(String(255))
    external_board_id: Mapped[str | None] = mapped_column(String(255))
    webhook_secret_hash: Mapped[str | None] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class ColumnMapping(Base, TimestampMixin):
    __tablename__ = "column_mappings"
    __table_args__ = (UniqueConstraint("board_integration_id", "task_status", name="uq_board_status_mapping"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    board_integration_id: Mapped[uuid.UUID] = uuid_fk("board_integrations.id")
    task_status: Mapped[str] = mapped_column(String(32), nullable=False)
    external_column_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_column_name: Mapped[str | None] = mapped_column(String(255))


class EmployeeBoardMapping(Base, TimestampMixin):
    __tablename__ = "employee_board_mappings"
    __table_args__ = (UniqueConstraint("board_integration_id", "employee_id", name="uq_employee_board_mapping"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    board_integration_id: Mapped[uuid.UUID] = uuid_fk("board_integrations.id")
    employee_id: Mapped[uuid.UUID] = uuid_fk("employees.id")
    external_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_email: Mapped[str | None] = mapped_column(String(320))


class KomandusTask(Base, TimestampMixin):
    __tablename__ = "komandus_tasks"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    employee_id: Mapped[uuid.UUID | None] = uuid_fk("employees.id", nullable=True)
    department_id: Mapped[uuid.UUID | None] = uuid_fk("departments.id", nullable=True)
    team_id: Mapped[uuid.UUID | None] = uuid_fk("teams.id", nullable=True)
    organization_chat_id: Mapped[uuid.UUID | None] = uuid_fk("organization_chats.id", nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="DETECTED", nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime)
    source_chat_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    source_message_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    llm_confidence: Mapped[float | None] = mapped_column(Float)
    llm_model: Mapped[str | None] = mapped_column(String(128))
    extraction_version: Mapped[str | None] = mapped_column(String(64))
    external_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    external_task_url: Mapped[str | None] = mapped_column(String(1024))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    source_excerpt: Mapped[str | None] = mapped_column(Text)


class TaskConfirmation(Base, TimestampMixin):
    __tablename__ = "task_confirmations"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    task_id: Mapped[uuid.UUID] = uuid_fk("komandus_tasks.id")
    employee_id: Mapped[uuid.UUID | None] = uuid_fk("employees.id", nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    decline_reason: Mapped[str | None] = mapped_column(Text)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime)




class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    user_id: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    employee_id: Mapped[uuid.UUID | None] = uuid_fk("employees.id", nullable=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class ProfileNote(Base, TimestampMixin):
    __tablename__ = "profile_notes"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    user_id: Mapped[uuid.UUID] = uuid_fk("users.id")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(128))
    meeting_id: Mapped[str | None] = mapped_column(String(128))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID | None] = uuid_fk("organizations.id", nullable=True)
    user_id: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    request_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"
    __table_args__ = (UniqueConstraint("provider", "event_id", name="uq_provider_event"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (UniqueConstraint("organization_id", "snapshot_date", "kind", name="uq_snapshot_kind_date"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = uuid_fk("organizations.id")
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
