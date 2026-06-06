import pytest

pytest.importorskip("fastapi")

from app.common.enums import Permission, Role
from app.common.rbac import has_permission, normalize_role, permission_values_for_role, validate_role_for_write
from app.telegram.service import TelegramService


def test_role_permissions_use_five_system_roles_and_scopes():
    assert [role.value for role in Role] == ["OWNER", "ADMIN", "MANAGER", "EMPLOYEE", "OBSERVER"]
    assert has_permission(Role.OWNER, Permission.CAN_VIEW_AUDIT_LOGS)
    assert has_permission(Role.ADMIN, Permission.CAN_MANAGE_USERS)
    assert has_permission(Role.MANAGER, Permission.CAN_ASSIGN_TASKS)
    assert has_permission(Role.OBSERVER, Permission.CAN_VIEW_ANALYTICS)
    assert not has_permission(Role.EMPLOYEE, Permission.CAN_CREATE_EMPLOYEE)


def test_legacy_roles_are_read_compatible_but_rejected_on_write():
    assert normalize_role("ORG_OWNER") == Role.OWNER
    assert normalize_role("DEPARTMENT_MANAGER") == Role.MANAGER
    assert normalize_role("TEAM_LEAD") == Role.MANAGER
    assert normalize_role("PRODUCT_MANAGER") == Role.ADMIN
    assert normalize_role("VIEWER") == Role.OBSERVER
    assert Permission.CAN_MANAGE_INTEGRATIONS.value in permission_values_for_role("PRODUCT_MANAGER")
    for forbidden in ["ORG_OWNER", "DEPARTMENT_MANAGER", "TEAM_LEAD", "PRODUCT_MANAGER", "VIEWER", "HR_MANAGER", "SALES_MANAGER"]:
        with pytest.raises(ValueError, match="Use Position"):
            validate_role_for_write(forbidden)


def test_telegram_button_urls_require_https_public_host(monkeypatch):
    import app.telegram.service as telegram_service

    object.__setattr__(telegram_service.settings, "APP_PUBLIC_URL", "https://app.komandus.ai")
    service = TelegramService(token="dummy")

    assert service.is_allowed_button_url("https://app.komandus.ai/auth/magic-login?token=x")
    assert not service.is_allowed_button_url("http://localhost:3000")
    assert not service.is_allowed_button_url("https://evil.example/auth/magic-login?token=x")
