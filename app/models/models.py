from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_message_id: Mapped[int]

    telegram_user_id: Mapped[int]

    chat_id: Mapped[int]

    text: Mapped[str]

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


class TaskCandidate(Base):
    __tablename__ = "task_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)

    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id")
    )

    title: Mapped[str]

    assignee_raw: Mapped[str | None]

    deadline_raw: Mapped[str | None]

    confidence: Mapped[float]

    status: Mapped[str] = mapped_column(
        default="pending"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_candidates.id")
    )

    title: Mapped[str]

    description: Mapped[str | None]

    assignee_id: Mapped[str | None]

    status: Mapped[str] = mapped_column(
        default="todo"
    )

    priority: Mapped[str] = mapped_column(
        default="medium"
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )