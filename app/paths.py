"""Resolução de caminhos de recursos (dev e PyInstaller frozen) e dados do usuário."""

from __future__ import annotations

import os
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


def user_data_dir() -> Path:
    """
    Diretório de preferências e perfis do usuário (por SO).

    - Windows: %APPDATA%/Clickr
    - macOS: ~/Library/Application Support/Clickr
    - Linux: $XDG_CONFIG_HOME/Clickr ou ~/.config/Clickr
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("Variável APPDATA não definida")
        return Path(appdata) / "Clickr"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Clickr"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "Clickr"
    return Path.home() / ".config" / "Clickr"
