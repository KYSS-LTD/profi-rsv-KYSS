from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.common.enums import Permission, PermissionScope, Role

ALLOWED_ROLE_VALUES = {role.value for role in Role}
LEGACY_ROLE_MAP: dict[str, Role] = {
    "SUPER_ADMIN": Role.OWNER,
    "ORG_OWNER": Role.OWNER,
    "DEPARTMENT_MANAGER": Role.MANAGER,
    "TEAM_LEAD": Role.MANAGER,
    "PRODUCT_MANAGER": Role.ADMIN,
    "VIEWER": Role.OBSERVER,
}
FORBIDDEN_BUSINESS_ROLE_VALUES = set(LEGACY_ROLE_MAP) | {
    "HR_MANAGER",
    "SALES_MANAGER",
    "REGIONAL_MANAGER",
    "SENIOR_MANAGER",
}

ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OWNER: set(Permission),
    Role.ADMIN: {
        Permission.CAN_CREATE_EMPLOYEE,
        Permission.CAN_EDIT_EMPLOYEE,
        Permission.CAN_DISABLE_EMPLOYEE,
        Permission.CAN_ASSIGN_TASKS,
        Permission.CAN_MANAGE_BOARDS,
        Permission.CAN_MANAGE_INTEGRATIONS,
        Permission.CAN_VIEW_ANALYTICS,
        Permission.CAN_MANAGE_DEPARTMENTS,
        Permission.CAN_MANAGE_TEAMS,
        Permission.CAN_OVERRIDE_LLM,
        Permission.CAN_VIEW_AUDIT_LOGS,
        Permission.CAN_MANAGE_USERS,
        Permission.CAN_MANAGE_HIERARCHY,
        Permission.CAN_MANAGE_PERMISSIONS,
    },
    Role.MANAGER: {
        Permission.CAN_CREATE_EMPLOYEE,
        Permission.CAN_EDIT_EMPLOYEE,
        Permission.CAN_DISABLE_EMPLOYEE,
        Permission.CAN_ASSIGN_TASKS,
        Permission.CAN_VIEW_ANALYTICS,
        Permission.CAN_MANAGE_BOARDS,
        Permission.CAN_MANAGE_INTEGRATIONS,
        Permission.CAN_MANAGE_TEAMS,
    },
    Role.EMPLOYEE: set(),
    Role.OBSERVER: {Permission.CAN_VIEW_ANALYTICS},
}

ROLE_DEFAULT_SCOPES: dict[Role, set[PermissionScope]] = {
    Role.OWNER: set(PermissionScope),
    Role.ADMIN: {PermissionScope.USERS, PermissionScope.TASKS, PermissionScope.ANALYTICS, PermissionScope.DEPARTMENTS, PermissionScope.INTEGRATIONS, PermissionScope.SETTINGS},
    Role.MANAGER: {PermissionScope.USERS, PermissionScope.TASKS, PermissionScope.ANALYTICS, PermissionScope.DEPARTMENTS},
    Role.EMPLOYEE: {PermissionScope.TASKS},
    Role.OBSERVER: {PermissionScope.ANALYTICS},
}

ROLE_ORDER = {Role.OBSERVER: 10, Role.EMPLOYEE: 20, Role.MANAGER: 50, Role.ADMIN: 80, Role.OWNER: 100}


def normalize_role(role: str | Role) -> Role:
    """Normalize persisted roles into the five-role model without data loss.

    Runtime authorization remains backward-compatible for tenants that still have
    legacy role strings in historical rows. New writes must use
    :func:`validate_role_for_write`, so business titles never become RBAC roles.
    """
    if isinstance(role, Role):
        return role
    value = str(role)
    if value not in ALLOWED_ROLE_VALUES:
        raise ValueError(f"Unsupported Komandus role: {value}. Use Position for business titles.")
    return Role(value)


def validate_role_for_write(role: str | Role) -> Role:
    """Validate a role provided by a create/update API.

    Only OWNER, ADMIN, MANAGER, EMPLOYEE, and OBSERVER are accepted. Legacy
    manager-like values and business titles must be stored as Position instead.
    """
    if isinstance(role, Role):
        return role
    value = str(role)
    if value in FORBIDDEN_BUSINESS_ROLE_VALUES or value not in ALLOWED_ROLE_VALUES:
        raise ValueError(f"Unsupported Komandus role: {value}. Use Position for business titles.")
    return Role(value)


def role_value(role: str | Role) -> str:
    return normalize_role(role).value


def permissions_for_role(role: str | Role) -> set[Permission]:
    return ROLE_PERMISSIONS[normalize_role(role)]


def permission_values_for_role(role: str | Role) -> list[str]:
    return sorted(permission.value for permission in permissions_for_role(role))


def scopes_for_role(role: str | Role) -> set[PermissionScope]:
    return ROLE_DEFAULT_SCOPES[normalize_role(role)]


def has_permission(role: str | Role, permission: Permission) -> bool:
    return permission in permissions_for_role(role)


class RoleChecker:
    def __init__(self, *allowed_roles: Role):
        self.allowed_roles = {normalize_role(role) for role in allowed_roles}

    def __call__(self, current_user=Depends(get_current_user)):
        user_role = normalize_role(current_user.role)
        if user_role in self.allowed_roles or user_role == Role.OWNER:
            return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")


class PermissionChecker:
    def __init__(self, *required_permissions: Permission):
        self.required_permissions = set(required_permissions)

    def __call__(self, current_user=Depends(get_current_user)):
        granted = permissions_for_role(current_user.role)
        missing = self.required_permissions - granted
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"missing_permissions": sorted(permission.value for permission in missing)})
        return current_user
