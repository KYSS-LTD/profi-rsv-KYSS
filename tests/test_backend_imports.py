import importlib
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def iter_backend_modules() -> list[str]:
    return [
        path.with_suffix("").relative_to(APP_DIR.parent).as_posix().replace("/", ".")
        for path in sorted(APP_DIR.rglob("*.py"))
    ]


def test_all_backend_modules_import_cleanly():
    """Catch invalid top-level imports before uvicorn/celery startup fails."""
    pytest.importorskip("fastapi")
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("pydantic_settings")
    pytest.importorskip("celery")
    pytest.importorskip("httpx")
    failures: dict[str, str] = {}

    for module_name in iter_backend_modules():
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - assertion message path
            failures[module_name] = f"{type(exc).__name__}: {exc}"

    assert failures == {}
