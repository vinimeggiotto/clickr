"""WindowFilter — só permite clique se a janela em foco casar com o critério."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from typing import Optional

from core.types import WindowFilterConfig

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class WindowFilter:
    """
    Regra ativa: se enabled e critérios definidos, `allows()` exige
    processo e/ou substring no título da janela em foco.
    """

    def __init__(self) -> None:
        self._config = WindowFilterConfig()
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._setup_apis()

    def _setup_apis(self) -> None:
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
        """
        cfg = self._config
        if not cfg.enabled:
            return True

        want_process = (cfg.process or "").strip().lower()
        want_title = (cfg.title_contains or "").strip().lower()
        if not want_process and not want_title:
            return True

        hwnd = self._GetForegroundWindow()
        if not hwnd:
            return False

        if want_title:
            title = self._window_title(hwnd).lower()
            if want_title not in title:
                return False

        if want_process:
            exe = self._process_name(hwnd)
            if exe is None:
                return False
            if not self._process_matches(exe, want_process):
                return False

        return True

    def _window_title(self, hwnd: int) -> str:
        length = self._GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        self._GetWindowTextW(hwnd, buf, length + 1)
        return buf.value or ""

    def _process_name(self, hwnd: int) -> Optional[str]:
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
                # Buffer curto — tenta maior
                size = wintypes.DWORD(1024)
                buf = ctypes.create_unicode_buffer(size.value)
                if not self._QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                    return None
            path = buf.value or ""
            return os.path.basename(path)
        finally:
            self._CloseHandle(handle)

    @staticmethod
    def _process_matches(exe_name: str, wanted: str) -> bool:
        """Aceita 'notepad', 'notepad.exe' (case-insensitive)."""
        exe = exe_name.lower()
        want = wanted.lower().strip()
        if not want:
            return True
        if exe == want:
            return True
        if want.endswith(".exe"):
            return exe == want
        return exe == want or exe == f"{want}.exe"
