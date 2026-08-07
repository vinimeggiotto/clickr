"""Resolução de caminhos de recursos (dev e PyInstaller frozen)."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """
    Raiz dos recursos empacotados.

    Em build PyInstaller one-file/one-dir, usa sys._MEIPASS.
    Em desenvolvimento, usa a pasta do repositório (pai de app/).
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def ui_dir() -> Path:
    return project_root() / "ui"


def assets_dir() -> Path:
    return project_root() / "assets"


def locales_dir() -> Path:
    return ui_dir() / "locales"
