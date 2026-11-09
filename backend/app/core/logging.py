"""Logging setup for the backend (replaces ad-hoc print() calls)."""

import logging

LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
DATE_FORMAT = "%H:%M:%S"


def configure_logging(level: str | int = "INFO") -> None:
    """Configure the root logger once; safe to call repeatedly."""
    if isinstance(level, str):
        level = logging.getLevelName(level.upper())
        if not isinstance(level, int):
            level = logging.INFO

    root = logging.getLogger()
    if not any(getattr(h, "_app_handler", False) for h in root.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        handler._app_handler = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    root.setLevel(level)
