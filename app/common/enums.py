from enum import StrEnum


class Role(StrEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ORG_OWNER = "ORG_OWNER"
    MANAGER = "MANAGER"  # Backward-compatible alias for legacy org owner accounts.
    DEPARTMENT_MANAGER = "DEPARTMENT_MANAGER"
    TEAM_LEAD = "TEAM_LEAD"
    PRODUCT_MANAGER = "PRODUCT_MANAGER"
    EMPLOYEE = "EMPLOYEE"
    VIEWER = "VIEWER"


class Permission(StrEnum):
    CAN_CREATE_EMPLOYEE = "can_create_employee"
    CAN_EDIT_EMPLOYEE = "can_edit_employee"
    CAN_DISABLE_EMPLOYEE = "can_disable_employee"
    CAN_ASSIGN_TASKS = "can_assign_tasks"
    CAN_MANAGE_BOARDS = "can_manage_boards"
    CAN_MANAGE_INTEGRATIONS = "can_manage_integrations"
    CAN_VIEW_ANALYTICS = "can_view_analytics"
    CAN_MANAGE_DEPARTMENTS = "can_manage_departments"
    CAN_MANAGE_TEAMS = "can_manage_teams"
    CAN_OVERRIDE_LLM = "can_override_llm"
    CAN_VIEW_AUDIT_LOGS = "can_view_audit_logs"


class TaskStatus(StrEnum):
    DETECTED = "DETECTED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    TO_DO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"
    OVERDUE = "OVERDUE"


class ConfirmationStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
