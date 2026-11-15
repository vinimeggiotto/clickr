"""Instância única do aplicativo + pedido de "mostrar janela" entre processos."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Optional

from app.paths import user_data_dir

_MUTEX_NAME = "Local\\Clickr.SingleInstance.v1"
_ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    """
    acquire() → True se este processo é o único Clickr em execução.

    - Windows: mutex nomeado.
    - macOS / Linux: flock em {user_data_dir}/clickr.lock.
    Um segundo processo chama request_show() e encerra; o primeiro observa o
    arquivo de pedido (watch) e traz a janela para frente.
    """

    def __init__(self, directory: Optional[Path] = None) -> None:
        self._dir = Path(directory) if directory is not None else user_data_dir()
        self._handle: Any = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def _request_path(self) -> Path:
        return self._dir / "show.request"

    def acquire(self) -> bool:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            return True  # sem diretório não há como coordenar; não bloqueia o app
        if sys.platform == "win32":
            return self._acquire_win32()
        return self._acquire_posix()

    def _acquire_win32(self) -> bool:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        ctypes.set_last_error(0)
        handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        if not handle:
            return True
        if ctypes.get_last_error() == _ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        self._handle = handle
        return True

    def _acquire_posix(self) -> bool:
        import fcntl

        try:
            handle = open(self._dir / "clickr.lock", "a+")
        except OSError:
            return True
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return False
        self._handle = handle
        return True

    def request_show(self) -> None:
        """Chamado pela segunda instância antes de encerrar."""
        try:
            self._request_path.write_text(str(os.getpid()), encoding="utf-8")
        except OSError:
            pass

    def watch(self, on_show: Callable[[], None], interval_s: float = 0.5) -> None:
        """Na instância principal: observa pedidos de exibição."""
        if self._thread is not None:
            return
        try:
            self._request_path.unlink()
        except OSError:
            pass

        def run() -> None:
            while not self._stop.wait(interval_s):
                path = self._request_path
                if not path.exists():
                    continue
                try:
                    path.unlink()
                except OSError:
                    pass
                try:
                    on_show()
                except Exception:
                    pass

        self._thread = threading.Thread(target=run, name="SingleInstanceWatch", daemon=True)
        self._thread.start()

    def release(self) -> None:
        self._stop.set()
        handle, self._handle = self._handle, None
        if handle is None:
            return
        try:
            if sys.platform == "win32":
                import ctypes

                ctypes.WinDLL("kernel32").CloseHandle(handle)
            else:
                handle.close()
        except Exception:
            pass
