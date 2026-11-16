"""Backend de hotkeys do Windows via RegisterHotKey.

A tecla registrada é consumida pelo sistema e não chega ao programa em foco.
Combos que o Windows recusa (já usados por outro programa ou reservados) caem
no backend pynput como reserva, para o atalho continuar funcionando.
"""

from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable, Optional

from app.log import get_logger
from hotkeys.backend_pynput import PynputHotkeyBackend
from hotkeys.combo import Combo

log = get_logger()

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_QUIT = 0x0012
WM_HOTKEY = 0x0312
WM_USER = 0x0400
WM_APP_APPLY = 0x8001
PM_NOREMOVE = 0x0000

_MOD_FLAGS = {"ALT": MOD_ALT, "CTRL": MOD_CONTROL, "SHIFT": MOD_SHIFT, "WIN": MOD_WIN}


class Win32HotkeyBackend:
    def __init__(self, on_action: Callable[[str], None]) -> None:
        self._on_action = on_action
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._user32.RegisterHotKey.argtypes = (
            wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT,
        )
        self._user32.RegisterHotKey.restype = wintypes.BOOL
        self._user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
        self._user32.UnregisterHotKey.restype = wintypes.BOOL
        self._user32.GetMessageW.argtypes = (
            ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT,
        )
        self._user32.GetMessageW.restype = ctypes.c_int
        self._user32.PeekMessageW.argtypes = (
            ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT,
            wintypes.UINT,
        )
        self._user32.PostThreadMessageW.argtypes = (
            wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
        )
        self._user32.PostThreadMessageW.restype = wintypes.BOOL
        self._user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
        self._user32.GetAsyncKeyState.restype = ctypes.c_short
        self._kernel32.GetCurrentThreadId.restype = wintypes.DWORD

        self._lock = threading.Lock()
        self._desired: dict[str, Combo] = {}
        self._registered: dict[int, str] = {}
        self._failed: dict[str, str] = {}
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._thread_id = 0
        self._ready = threading.Event()
        self._applied = threading.Event()
        self._fallback = PynputHotkeyBackend(on_action)
        self._fallback_started = False

    # --- API ------------------------------------------------------------

    def start(self) -> None:
        if self._thread is not None:
            return
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, name="HotkeysWin32", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=2.0)
        self._request_apply()

    def stop(self) -> None:
        thread, self._thread = self._thread, None
        if thread is not None and self._thread_id:
            self._user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            thread.join(timeout=2.0)
        if self._fallback_started:
            self._fallback.stop()
            self._fallback_started = False

    def apply(self, bindings: dict[str, Combo]) -> dict[str, str]:
        """Registra os combos. Retorna {ação: combo} dos que usam a reserva pynput."""
        with self._lock:
            self._desired = dict(bindings)
        self._request_apply()
        with self._lock:
            return dict(self._failed)

    def pause(self) -> None:
        self._paused = True
        self._fallback.pause()
        self._request_apply()

    def resume(self) -> None:
        self._paused = False
        self._fallback.resume()
        self._request_apply()

    def is_pressed(self, combo: Combo) -> bool:
        return bool(self._user32.GetAsyncKeyState(int(combo.vk)) & 0x8000)

    # --- Thread de mensagens ---------------------------------------------

    def _request_apply(self) -> None:
        if self._thread is None or not self._thread_id:
            return
        self._applied.clear()
        if self._user32.PostThreadMessageW(self._thread_id, WM_APP_APPLY, 0, 0):
            self._applied.wait(timeout=1.0)

    def _run(self) -> None:
        msg = wintypes.MSG()
        # Cria a fila de mensagens da thread antes de sinalizar que está pronta.
        self._user32.PeekMessageW(ctypes.byref(msg), None, WM_USER, WM_USER, PM_NOREMOVE)
        self._thread_id = int(self._kernel32.GetCurrentThreadId())
        self._ready.set()
        try:
            while self._user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    action = self._registered.get(int(msg.wParam))
                    if action is not None:
                        try:
                            self._on_action(action)
                        except Exception:
                            log.exception("Falha ao despachar atalho %s", action)
                elif msg.message == WM_APP_APPLY:
                    self._register_all()
                    self._applied.set()
        finally:
            self._unregister_all()
            self._thread_id = 0

    def _unregister_all(self) -> None:
        for hotkey_id in list(self._registered):
            self._user32.UnregisterHotKey(None, hotkey_id)
        self._registered.clear()

    def _register_all(self) -> None:
        self._unregister_all()
        with self._lock:
            desired = dict(self._desired)
        failed: dict[str, Combo] = {}
        if not self._paused:
            for index, (action, combo) in enumerate(desired.items(), start=1):
                flags = MOD_NOREPEAT
                for mod in combo.mods:
                    flags |= _MOD_FLAGS[mod]
                if self._user32.RegisterHotKey(None, index, flags, int(combo.vk)):
                    self._registered[index] = action
                else:
                    log.warning("RegisterHotKey recusou %s (%s); usando reserva", combo, action)
                    failed[action] = combo
        with self._lock:
            self._failed = {action: str(combo) for action, combo in failed.items()}
        self._fallback.apply(failed)
        if failed and not self._fallback_started:
            try:
                self._fallback.start()
                self._fallback_started = True
            except Exception:
                log.exception("Reserva pynput de hotkeys indisponível")
