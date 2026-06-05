from app.common.enums import TaskStatus

ALLOWED_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.DETECTED: {TaskStatus.PENDING_CONFIRMATION, TaskStatus.ACCEPTED, TaskStatus.REJECTED},
    TaskStatus.PENDING_CONFIRMATION: {TaskStatus.ACCEPTED, TaskStatus.REJECTED},
    TaskStatus.ACCEPTED: {TaskStatus.TO_DO},
    TaskStatus.TO_DO: {TaskStatus.IN_PROGRESS, TaskStatus.OVERDUE},
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW, TaskStatus.DONE, TaskStatus.OVERDUE},
    TaskStatus.REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.OVERDUE},
    TaskStatus.DONE: set(),
    TaskStatus.REJECTED: set(),
    TaskStatus.OVERDUE: {TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.DONE},
}


def assert_valid_transition(old_status: str, new_status: str) -> None:
    old = TaskStatus(old_status)
    new = TaskStatus(new_status)
    if new not in ALLOWED_TASK_TRANSITIONS[old]:
        raise ValueError(f"Invalid task transition: {old.value} -> {new.value}")
