import pytest

pytest.importorskip("fastapi")

from app.common.enums import Permission, Role
from app.common.rbac import has_permission, normalize_role, permission_values_for_role
from app.telegram.service import TelegramService


def test_role_permissions_include_hierarchy_manager_capabilities():
    assert has_permission(Role.ORG_OWNER, Permission.CAN_VIEW_AUDIT_LOGS)
    assert has_permission(Role.DEPARTMENT_MANAGER, Permission.CAN_MANAGE_TEAMS)
    assert has_permission(Role.TEAM_LEAD, Permission.CAN_ASSIGN_TASKS)
    assert not has_permission(Role.EMPLOYEE, Permission.CAN_CREATE_EMPLOYEE)


def test_legacy_manager_normalizes_to_org_owner():
    assert normalize_role(Role.MANAGER) == Role.ORG_OWNER
    assert Permission.CAN_MANAGE_INTEGRATIONS.value in permission_values_for_role(Role.MANAGER)


def test_telegram_button_urls_require_https_public_host(monkeypatch):
    import app.telegram.service as telegram_service

    object.__setattr__(telegram_service.settings, "APP_PUBLIC_URL", "https://app.komandus.ai")
    service = TelegramService(token="dummy")

    assert service.is_allowed_button_url("https://app.komandus.ai/auth/magic-login?token=x")
    assert not service.is_allowed_button_url("http://localhost:3000")
    assert not service.is_allowed_button_url("https://evil.example/auth/magic-login?token=x")
