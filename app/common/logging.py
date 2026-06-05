from __future__ import annotations

import logging
try:
    import structlog
except ImportError:  # pragma: no cover
    structlog = None


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if structlog is not None:
        structlog.configure(
            processors=[structlog.contextvars.merge_contextvars, structlog.processors.add_log_level, structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            cache_logger_on_first_use=True,
        )
