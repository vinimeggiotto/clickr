"""WindowFilter — só permite clique se a janela em foco casar com o critério."""

from __future__ import annotations

import ctypes
import os
import re
import shutil
import subprocess
import sys
from ctypes import wintypes
from typing import Optional

from core.types import WindowFilterConfig

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class WindowFilter:
    """
    Regra ativa: se enabled e critérios definidos, `allows()` exige
    processo e/ou substring no título da janela em foco.

    Backends:
    - Windows: Win32 (GetForegroundWindow)
    - macOS: osascript / System Events
    - Linux: xprop (+ xdotool opcional para título); erro explícito se ausentes
    """

    def __init__(self) -> None:
        self._config = WindowFilterConfig()
        if sys.platform == "win32":
            self._user32 = ctypes.WinDLL("user32", use_last_error=True)
            self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            self._setup_win32_apis()

    def _setup_win32_apis(self) -> None:
        self._GetForegroundWindow = self._user32.GetForegroundWindow
        self._GetForegroundWindow.restype = wintypes.HWND

        self._GetWindowTextLengthW = self._user32.GetWindowTextLengthW
        self._GetWindowTextLengthW.argtypes = (wintypes.HWND,)
        self._GetWindowTextLengthW.restype = ctypes.c_int

        self._GetWindowTextW = self._user32.GetWindowTextW
        self._GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
        self._GetWindowTextW.restype = ctypes.c_int

        self._GetWindowThreadProcessId = self._user32.GetWindowThreadProcessId
        self._GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
        self._GetWindowThreadProcessId.restype = wintypes.DWORD

        self._OpenProcess = self._kernel32.OpenProcess
        self._OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        self._OpenProcess.restype = wintypes.HANDLE

        self._CloseHandle = self._kernel32.CloseHandle
        self._CloseHandle.argtypes = (wintypes.HANDLE,)
        self._CloseHandle.restype = wintypes.BOOL

        self._QueryFullProcessImageNameW = self._kernel32.QueryFullProcessImageNameW
        self._QueryFullProcessImageNameW.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        )
        self._QueryFullProcessImageNameW.restype = wintypes.BOOL

    def configure(self, config: WindowFilterConfig) -> None:
        self._config = WindowFilterConfig(
            enabled=bool(config.enabled),
            process=str(config.process or ""),
            title_contains=str(config.title_contains or ""),
        )

    def get_config(self) -> WindowFilterConfig:
        return WindowFilterConfig(**self._config.to_dict())

    def allows(self) -> bool:
        """
        True se o clique pode ocorrer.

        - Filtro desligado → True
        - Ligado sem critérios → True
        - Ligado com process e/ou title_contains → todos os critérios não vazios devem casar
        - Falha ao consultar janela ativa (ferramenta ausente / erro OS) → OSError explícito
        """
        cfg = self._config
        if not cfg.enabled:
            return True

        want_process = (cfg.process or "").strip().lower()
        want_title = (cfg.title_contains or "").strip().lower()
        if not want_process and not want_title:
            return True

        process_name, title = self._foreground_info()

        if want_title:
            if want_title not in (title or "").lower():
                return False

        if want_process:
            if process_name is None:
                return False
            if not self._process_matches(process_name, want_process):
                return False

        return True

    def _foreground_info(self) -> tuple[Optional[str], str]:
        """Retorna (nome_processo_ou_app, título). Levanta OSError se indisponível."""
        if sys.platform == "win32":
            return self._foreground_win32()
        if sys.platform == "darwin":
            return self._foreground_darwin()
        return self._foreground_linux()

    def _foreground_win32(self) -> tuple[Optional[str], str]:
        hwnd = self._GetForegroundWindow()
        if not hwnd:
            return None, ""
        title = self._window_title_win32(hwnd)
        exe = self._process_name_win32(hwnd)
        return exe, title

    def _window_title_win32(self, hwnd: int) -> str:
        length = self._GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        self._GetWindowTextW(hwnd, buf, length + 1)
        return buf.value or ""

    def _process_name_win32(self, hwnd: int) -> Optional[str]:
        pid = wintypes.DWORD(0)
        self._GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return None
        handle = self._OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return None
        try:
            size = wintypes.DWORD(260)
            buf = ctypes.create_unicode_buffer(size.value)
            if not self._QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                size = wintypes.DWORD(1024)
                buf = ctypes.create_unicode_buffer(size.value)
                if not self._QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                    return None
            path = buf.value or ""
            return os.path.basename(path)
        finally:
            self._CloseHandle(handle)

    def _foreground_darwin(self) -> tuple[Optional[str], str]:
        script = (
            'tell application "System Events"\n'
            "  set frontApp to first application process whose frontmost is true\n"
            "  set appName to name of frontApp\n"
            '  set winTitle to ""\n'
            "  try\n"
            "    set winTitle to name of front window of frontApp\n"
            "  end try\n"
            '  return appName & linefeed & winTitle\n'
            "end tell"
        )
        try:
            completed = subprocess.run(
                ["osascript", "-e", script],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except FileNotFoundError as exc:
            raise OSError(
                "osascript não encontrado. Necessário para o filtro de janela no macOS."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise OSError("osascript excedeu o tempo ao consultar a janela ativa.") from exc

        if completed.returncode != 0:
            err = (completed.stderr or completed.stdout or "").strip()
            raise OSError(
                "Falha ao consultar janela ativa via osascript"
                + (f": {err}" if err else ".")
            )

        out = (completed.stdout or "").rstrip("\n")
        parts = out.split("\n", 1)
        app_name = parts[0].strip() if parts else ""
        title = parts[1].strip() if len(parts) > 1 else ""
        return (app_name or None), title

    def _foreground_linux(self) -> tuple[Optional[str], str]:
        if shutil.which("xprop") is None:
            raise OSError(
                "Ferramenta 'xprop' não encontrada. No Linux o filtro de janela "
                "exige xprop (pacote x11-utils). Instale-a ou desative o filtro."
            )

        window_id = self._linux_active_window_id()
        if not window_id:
            return None, ""

        process_name = self._linux_wm_class(window_id)
        title = self._linux_window_title(window_id)
        return process_name, title

    def _linux_active_window_id(self) -> Optional[str]:
        try:
            completed = subprocess.run(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except subprocess.TimeoutExpired as exc:
            raise OSError("xprop excedeu o tempo ao ler _NET_ACTIVE_WINDOW.") from exc

        if completed.returncode != 0:
            err = (completed.stderr or completed.stdout or "").strip()
            raise OSError(
                "Falha ao ler janela ativa via xprop"
                + (f": {err}" if err else ".")
            )

        # Formato típico: _NET_ACTIVE_WINDOW(WINDOW): window id # 0x3c00007
        match = re.search(r"0x[0-9a-fA-F]+", completed.stdout or "")
        if not match:
            return None
        wid = match.group(0)
        if wid.lower() in ("0x0", "0x00"):
            return None
        return wid

    def _linux_wm_class(self, window_id: str) -> Optional[str]:
        try:
            completed = subprocess.run(
                ["xprop", "-id", window_id, "WM_CLASS"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except subprocess.TimeoutExpired as exc:
            raise OSError("xprop excedeu o tempo ao ler WM_CLASS.") from exc

        if completed.returncode != 0:
            err = (completed.stderr or completed.stdout or "").strip()
            raise OSError(
                "Falha ao ler WM_CLASS via xprop"
                + (f": {err}" if err else ".")
            )

        # WM_CLASS(STRING) = "gnome-terminal", "Gnome-terminal"
        match = re.search(r'=\s*"([^"]*)"\s*,\s*"([^"]*)"', completed.stdout or "")
        if not match:
            match_one = re.search(r'=\s*"([^"]*)"', completed.stdout or "")
            if not match_one:
                return None
            return match_one.group(1)
        # Preferência: instância (primeiro) — comum para match de processo
        return match.group(1) or match.group(2) or None

    def _linux_window_title(self, window_id: str) -> str:
        # Preferir xdotool se disponível; senão _NET_WM_NAME / WM_NAME via xprop
        if shutil.which("xdotool") is not None:
            try:
                completed = subprocess.run(
                    ["xdotool", "getwindowname", window_id],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            except subprocess.TimeoutExpired as exc:
                raise OSError("xdotool excedeu o tempo ao ler o título.") from exc
            if completed.returncode == 0:
                return (completed.stdout or "").rstrip("\n")
            err = (completed.stderr or completed.stdout or "").strip()
            raise OSError(
                "Falha ao ler título via xdotool"
                + (f": {err}" if err else ".")
            )

        for prop in ("_NET_WM_NAME", "WM_NAME"):
            try:
                completed = subprocess.run(
                    ["xprop", "-id", window_id, prop],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            except subprocess.TimeoutExpired as exc:
                raise OSError(f"xprop excedeu o tempo ao ler {prop}.") from exc
            if completed.returncode != 0:
                continue
            out = completed.stdout or ""
            if "not found" in out.lower():
                continue
            match = re.search(r'=\s*"(.*)"\s*$', out, re.DOTALL)
            if match:
                return match.group(1)
            # UTF8_STRING às vezes vem como = 0x..
            match_utf = re.search(r"=\s*(.+)$", out.strip())
            if match_utf and "not found" not in match_utf.group(1).lower():
                raw = match_utf.group(1).strip().strip('"')
                if raw:
                    return raw
        return ""

    @staticmethod
    def _process_matches(exe_name: str, wanted: str) -> bool:
        """
        Aceita match case-insensitive.

        Windows: 'notepad' ou 'notepad.exe'.
        macOS/Linux: nome do app / WM_CLASS (sem exigir .exe).
        """
        exe = exe_name.lower()
        want = wanted.lower().strip()
        if not want:
            return True
        if exe == want:
            return True
        if want.endswith(".exe"):
            return exe == want or exe == want[:-4]
        return exe == want or exe == f"{want}.exe"
