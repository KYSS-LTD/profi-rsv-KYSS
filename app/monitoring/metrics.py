from collections import Counter
from threading import Lock

_COUNTERS = Counter()
_LOCK = Lock()
KNOWN_COUNTERS = [
    "requests_total",
    "task_detection_total",
    "task_accept_total",
    "task_reject_total",
    "telegram_send_errors_total",
    "yougile_sync_errors_total",
]


def increment(name: str, value: int = 1) -> None:
    with _LOCK:
        _COUNTERS[name] += value


def render_prometheus() -> str:
    lines = []
    with _LOCK:
        values = {name: _COUNTERS.get(name, 0) for name in KNOWN_COUNTERS}
    for name, value in values.items():
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"
