"""Log do aplicativo em arquivo rotativo ({user_data_dir}/clickr.log)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

_LOGGER_NAME = "clickr"
_configured = False


def setup_logging() -> logging.Logger:
    """Configura o logger uma única vez. Falha de disco não derruba o app."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if _configured:
        return logger
    _configured = True
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        from app.paths import user_data_dir

        directory = user_data_dir()
        directory.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = RotatingFileHandler(
            directory / "clickr.log",
            maxBytes=512 * 1024,
            backupCount=2,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(message)s")
        )
    except Exception:
        handler = logging.NullHandler()
    logger.addHandler(handler)
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)
