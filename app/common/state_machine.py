from app.common.enums import TaskStatus

ALLOWED_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    # Tasks in any "new" sub-status share the kanban "Новые" column, so the board
    # must be able to pull them straight into work (→ IN_PROGRESS) as well as
    # confirm/reject them.
    TaskStatus.DETECTED: {TaskStatus.PENDING_CONFIRMATION, TaskStatus.ACCEPTED, TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.REJECTED},
    TaskStatus.PENDING_CONFIRMATION: {TaskStatus.ACCEPTED, TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.REJECTED},
    TaskStatus.ACCEPTED: {TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.REJECTED},
    TaskStatus.TO_DO: {TaskStatus.IN_PROGRESS, TaskStatus.OVERDUE, TaskStatus.REJECTED},
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW, TaskStatus.DONE, TaskStatus.TO_DO, TaskStatus.OVERDUE},
    TaskStatus.REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.OVERDUE},
    TaskStatus.DONE: {TaskStatus.IN_PROGRESS},
    TaskStatus.REJECTED: set(),
    TaskStatus.OVERDUE: {TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.DONE},
}


def assert_valid_transition(old_status: str, new_status: str) -> None:
    old = TaskStatus(old_status)
    new = TaskStatus(new_status)
    if new not in ALLOWED_TASK_TRANSITIONS[old]:
        raise ValueError(f"Invalid task transition: {old.value} -> {new.value}")
