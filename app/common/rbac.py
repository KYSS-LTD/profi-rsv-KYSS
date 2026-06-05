from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.common.enums import Permission, Role

ORG_OWNER_ROLES = {Role.ORG_OWNER, Role.MANAGER}

ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),
    Role.ORG_OWNER: set(Permission),
    Role.MANAGER: set(Permission),
    Role.DEPARTMENT_MANAGER: {
        Permission.CAN_CREATE_EMPLOYEE,
        Permission.CAN_EDIT_EMPLOYEE,
        Permission.CAN_DISABLE_EMPLOYEE,
        Permission.CAN_ASSIGN_TASKS,
        Permission.CAN_VIEW_ANALYTICS,
        Permission.CAN_MANAGE_TEAMS,
    },
    Role.TEAM_LEAD: {
        Permission.CAN_EDIT_EMPLOYEE,
        Permission.CAN_ASSIGN_TASKS,
        Permission.CAN_VIEW_ANALYTICS,
    },
    Role.PRODUCT_MANAGER: {
        Permission.CAN_ASSIGN_TASKS,
        Permission.CAN_MANAGE_BOARDS,
        Permission.CAN_MANAGE_INTEGRATIONS,
        Permission.CAN_VIEW_ANALYTICS,
        Permission.CAN_OVERRIDE_LLM,
    },
    Role.EMPLOYEE: set(),
    Role.VIEWER: {Permission.CAN_VIEW_ANALYTICS},
}

ROLE_ORDER = {
    Role.VIEWER: 10,
    Role.EMPLOYEE: 20,
    Role.PRODUCT_MANAGER: 30,
    Role.TEAM_LEAD: 32,
    Role.DEPARTMENT_MANAGER: 35,
    Role.MANAGER: 90,
    Role.ORG_OWNER: 90,
    Role.SUPER_ADMIN: 100,
}


def normalize_role(role: str | Role) -> Role:
    parsed = Role(role)
    return Role.ORG_OWNER if parsed == Role.MANAGER else parsed


def permissions_for_role(role: str | Role) -> set[Permission]:
    return ROLE_PERMISSIONS[Role(role)]


def permission_values_for_role(role: str | Role) -> list[str]:
    return sorted(permission.value for permission in permissions_for_role(role))


def has_permission(role: str | Role, permission: Permission) -> bool:
    return permission in permissions_for_role(role)


class RoleChecker:
    def __init__(self, *allowed_roles: Role):
        self.allowed_roles = {Role(role) for role in allowed_roles}

    def __call__(self, current_user=Depends(get_current_user)):
        user_role = Role(current_user.role)
        normalized_allowed = {normalize_role(role) for role in self.allowed_roles}
        if user_role == Role.SUPER_ADMIN or normalize_role(user_role) in normalized_allowed:
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
