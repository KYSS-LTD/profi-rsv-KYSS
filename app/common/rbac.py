from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.common.enums import Role


ROLE_ORDER = {
    Role.VIEWER: 10,
    Role.EMPLOYEE: 20,
    Role.PRODUCT_MANAGER: 30,
    Role.MANAGER: 40,
    Role.SUPER_ADMIN: 100,
}


class RoleChecker:
    def __init__(self, *allowed_roles: Role):
        self.allowed_roles = set(allowed_roles)

    def __call__(self, current_user=Depends(get_current_user)):
        user_role = Role(current_user.role)
        if user_role == Role.SUPER_ADMIN or user_role in self.allowed_roles:
            return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
