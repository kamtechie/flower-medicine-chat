from __future__ import annotations
import logging, sys
import structlog
from app.core.settings import settings

ENV = getattr(settings, "ENV", "dev").lower()  # dev|prod
LOG_LEVEL = getattr(settings, "LOG_LEVEL", "INFO").upper()

def setup_logging() -> None:
    """Configure stdlib + structlog. JSON in prod, pretty in dev."""
    # stdlib root
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    root.addHandler(handler)

    # structlog processors
    json_mode = (ENV == "prod")
    processors = [
        structlog.processors.TimeStamper(fmt="iso", key="ts"),
        structlog.processors.add_log_level,
        structlog.contextvars.merge_contextvars,  # ← pull correlation_id/session_id from contextvars
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        (structlog.processors.JSONRenderer() if json_mode else structlog.dev.ConsoleRenderer()),
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    get_logger("app.core.logging").info("Logging is set up", env=ENV, log_level=LOG_LEVEL)

def get_logger(name: str = "app"):
    return structlog.get_logger(name)
