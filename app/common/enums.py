from enum import StrEnum


class Role(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"
    OBSERVER = "OBSERVER"


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
    CAN_MANAGE_USERS = "can_manage_users"
    CAN_MANAGE_HIERARCHY = "can_manage_hierarchy"
    CAN_MANAGE_PERMISSIONS = "can_manage_permissions"
    CAN_MANAGE_BILLING = "can_manage_billing"
    CAN_DELETE_ORGANIZATION = "can_delete_organization"


class PermissionScope(StrEnum):
    USERS = "users"
    TASKS = "tasks"
    ANALYTICS = "analytics"
    DEPARTMENTS = "departments"
    INTEGRATIONS = "integrations"
    FINANCE = "finance"
    BILLING = "billing"
    SETTINGS = "settings"


class OrganizationMode(StrEnum):
    SIMPLE = "SIMPLE"
    HIERARCHY = "HIERARCHY"


class TaskSourceType(StrEnum):
    TELEGRAM_CHAT = "TELEGRAM_CHAT"
    TELEGRAM_TOPIC = "TELEGRAM_TOPIC"
    YOUGILE_BOARD = "YOUGILE_BOARD"
    YOUGILE_COLUMN = "YOUGILE_COLUMN"


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
