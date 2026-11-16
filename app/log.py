"""Log do aplicativo em arquivo rotativo ({user_data_dir}/clickr.log)."""

from __future__ import annotations

import faulthandler
import logging
import platform
import sys
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

_LOGGER_NAME = "clickr"
_configured = False
_watchdog_file: Optional[Any] = None


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
            logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(name)s: %(message)s")
        )
    except Exception:
        handler = logging.NullHandler()
    logger.addHandler(handler)
    # Erros internos do pywebview também vão para o arquivo (no exe não há console).
    webview_logger = logging.getLogger("pywebview")
    webview_logger.addHandler(handler)
    if webview_logger.level == logging.NOTSET or webview_logger.level > logging.WARNING:
        webview_logger.setLevel(logging.WARNING)
    logger.info("Iniciando %s", _environment_summary())
    return logger


def _environment_summary() -> str:
    parts = []
    try:
        from app.paths import app_version

        parts.append(f"Clickr {app_version()}")
    except Exception:
        parts.append("Clickr ?")
    parts.append(f"Python {platform.python_version()}")
    for package in ("pywebview", "pynput", "pystray", "pythonnet"):
        try:
            from importlib.metadata import version

            parts.append(f"{package} {version(package)}")
        except Exception:
            pass
    parts.append(platform.platform())
    if getattr(sys, "frozen", False):
        parts.append("frozen")
    return " | ".join(parts)


def arm_startup_watchdog(seconds: float = 20.0) -> None:
    """
    Se a interface não carregar em `seconds`, grava no log a pilha de TODAS as
    threads (faulthandler). Serve para diagnosticar travamentos na partida, que
    não geram exceção. Não encerra o processo.
    """
    global _watchdog_file
    if _watchdog_file is not None:
        return
    try:
        from app.paths import user_data_dir

        directory = user_data_dir()
        directory.mkdir(parents=True, exist_ok=True)
        _watchdog_file = open(directory / "clickr.log", "a", encoding="utf-8")
        _watchdog_file.write(
            f"--- watchdog armado: pilhas das threads serão gravadas abaixo se a "
            f"UI não carregar em {int(seconds)} s ---\n"
        )
        _watchdog_file.flush()
        faulthandler.dump_traceback_later(seconds, exit=False, file=_watchdog_file)
    except Exception:
        _watchdog_file = None


def disarm_startup_watchdog() -> None:
    """A interface carregou: cancela o despejo de pilhas."""
    global _watchdog_file
    handle, _watchdog_file = _watchdog_file, None
    if handle is None:
        return
    try:
        faulthandler.cancel_dump_traceback_later()
        handle.close()
    except Exception:
        pass


def watchdog_armed() -> bool:
    return _watchdog_file is not None


def get_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)
