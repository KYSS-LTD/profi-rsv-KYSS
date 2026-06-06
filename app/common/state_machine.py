from app.common.enums import TaskStatus

ALLOWED_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.DETECTED: {TaskStatus.PENDING_CONFIRMATION, TaskStatus.OPEN, TaskStatus.REJECTED, TaskStatus.CANCELLED},
    TaskStatus.PENDING_CONFIRMATION: {TaskStatus.OPEN, TaskStatus.REJECTED, TaskStatus.CANCELLED},
    TaskStatus.OPEN: {TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.OPEN, TaskStatus.DONE, TaskStatus.CANCELLED},
    TaskStatus.DONE: set(),
    TaskStatus.CANCELLED: set(),
    TaskStatus.REJECTED: set(),
}


def assert_valid_transition(old_status: str, new_status: str) -> None:
    old = TaskStatus(old_status)
    new = TaskStatus(new_status)
    if old == new:
        return
    if new not in ALLOWED_TASK_TRANSITIONS[old]:
        raise ValueError(f"Invalid task transition: {old.value} -> {new.value}")
