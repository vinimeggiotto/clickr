"""Iniciar o Clickr junto com a sessão do usuário (por SO, sem privilégios)."""

from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Optional

APP_NAME = "Clickr"
MINIMIZED_FLAG = "--minimized"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_MAC_LABEL = "com.clickr.app"


def launch_command() -> list[str]:
    """Comando que reabre este app minimizado na bandeja."""
    if getattr(sys, "frozen", False):
        return [sys.executable, MINIMIZED_FLAG]
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    return [sys.executable, str(main_py), MINIMIZED_FLAG]


def _mac_plist_path(home: Optional[Path] = None) -> Path:
    return (home or Path.home()) / "Library" / "LaunchAgents" / f"{_MAC_LABEL}.plist"


def _linux_desktop_path(home: Optional[Path] = None) -> Path:
    if home is None:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
    else:
        base = home / ".config"
    return base / "autostart" / "clickr.desktop"


def _desktop_quote(arg: str) -> str:
    """Aspas no padrão da chave Exec de arquivos .desktop."""
    if arg and all(ch.isalnum() or ch in "-_./=:@%+" for ch in arg):
        return arg
    escaped = arg.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return f'"{escaped}"'


def is_enabled(platform: Optional[str] = None, home: Optional[Path] = None) -> bool:
    platform = platform or sys.platform
    try:
        if platform == "win32":
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
                winreg.QueryValueEx(key, APP_NAME)
            return True
        if platform == "darwin":
            return _mac_plist_path(home).is_file()
        return _linux_desktop_path(home).is_file()
    except OSError:
        return False


def set_enabled(
    enabled: bool,
    platform: Optional[str] = None,
    home: Optional[Path] = None,
    command: Optional[list[str]] = None,
) -> None:
    """Ativa/desativa o início automático. Levanta OSError se o SO recusar."""
    platform = platform or sys.platform
    command = command or launch_command()
    if platform == "win32":
        _set_windows(enabled, command)
    elif platform == "darwin":
        _set_file(_mac_plist_path(home), enabled, _mac_plist(command))
    else:
        _set_file(_linux_desktop_path(home), enabled, _linux_desktop(command).encode("utf-8"))


def _set_windows(enabled: bool, command: list[str]) -> None:
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, subprocess.list2cmdline(command))
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def _set_file(path: Path, enabled: bool, content: bytes) -> None:
    if enabled:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _mac_plist(command: list[str]) -> bytes:
    return plistlib.dumps(
        {
            "Label": _MAC_LABEL,
            "ProgramArguments": list(command),
            "RunAtLoad": True,
            "ProcessType": "Interactive",
        }
    )


def _linux_desktop(command: list[str]) -> str:
    exec_line = " ".join(_desktop_quote(arg) for arg in command)
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        f"Exec={exec_line}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


__all__ = ["launch_command", "is_enabled", "set_enabled", "MINIMIZED_FLAG"]
