"""Registro e gravação de hotkey global via pynput."""

from __future__ import annotations

import threading
from typing import Callable, Optional, Union

from pynput import keyboard

KeyLike = Union[keyboard.Key, keyboard.KeyCode]


def format_key(key: object) -> Optional[str]:
    """Converte tecla pynput em nome estável (ex: F6, A, SPACE)."""
    if isinstance(key, keyboard.Key):
        name = key.name
        if name is None:
            return None
        # pynput usa f1..f12, space, etc.
        return name.replace("_", " ").upper()

    if isinstance(key, keyboard.KeyCode):
        if key.char and key.char.isprintable() and not key.char.isspace():
            return key.char.upper()
        if key.vk is not None:
            # VK_F1..VK_F12 = 0x70..0x7B
            if 0x70 <= key.vk <= 0x7B:
                return f"F{key.vk - 0x6F}"
        return None

    return None


def resolve_key(name: str) -> KeyLike:
    """Resolve nome de hotkey para objeto pynput comparável."""
    key_name = name.strip().upper()
    if not key_name:
        raise ValueError("Hotkey vazia")

    if key_name.startswith("F") and key_name[1:].isdigit():
        n = int(key_name[1:])
        if 1 <= n <= 24:
            return getattr(keyboard.Key, f"f{n}")

    special = {
        "SPACE": keyboard.Key.space,
        "ENTER": keyboard.Key.enter,
        "RETURN": keyboard.Key.enter,
        "TAB": keyboard.Key.tab,
        "ESC": keyboard.Key.esc,
        "ESCAPE": keyboard.Key.esc,
        "INSERT": keyboard.Key.insert,
        "DELETE": keyboard.Key.delete,
        "HOME": keyboard.Key.home,
        "END": keyboard.Key.end,
        "PAGE UP": keyboard.Key.page_up,
        "PAGEUP": keyboard.Key.page_up,
        "PAGE DOWN": keyboard.Key.page_down,
        "PAGEDOWN": keyboard.Key.page_down,
        "UP": keyboard.Key.up,
        "DOWN": keyboard.Key.down,
        "LEFT": keyboard.Key.left,
        "RIGHT": keyboard.Key.right,
        "PAUSE": keyboard.Key.pause,
        "SCROLL LOCK": keyboard.Key.scroll_lock,
        "PRINT SCREEN": keyboard.Key.print_screen,
    }
    if key_name in special:
        return special[key_name]

    if len(key_name) == 1:
        return keyboard.KeyCode.from_char(key_name.lower())

    raise ValueError(f"Hotkey não suportada: {name}")


class HotkeyService:
    """
    Escuta hotkey global e dispara callback no press.
    Suporta troca de tecla e gravação (captura da próxima tecla).
    """

    def __init__(self, on_toggle: Callable[[], None], hotkey: str = "F6") -> None:
        self._on_toggle = on_toggle
        self._hotkey_name = hotkey.upper()
        self._listener: Optional[keyboard.Listener] = None
        self._capture_listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()
        self._vk = resolve_key(self._hotkey_name)
        self._recording = False
        self._on_captured: Optional[Callable[[str], None]] = None

    def start(self) -> None:
        with self._lock:
            if self._listener is not None:
                return

            def on_press(key: object) -> None:
                if self._recording:
                    return
                if self._key_matches(key):
                    self._on_toggle()

            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.daemon = True
            self._listener.start()

    def stop(self) -> None:
        with self._lock:
            self._stop_capture_locked()
            if self._listener is None:
                return
            self._listener.stop()
            self._listener = None

    def set_hotkey(self, name: str) -> str:
        resolved = resolve_key(name)
        with self._lock:
            self._hotkey_name = format_key(resolved) or name.strip().upper()
            self._vk = resolved
            return self._hotkey_name

    def begin_capture(self, on_captured: Callable[[str], None]) -> None:
        """Inicia captura da próxima tecla pressionada."""
        with self._lock:
            self._stop_capture_locked()
            self._recording = True
            self._on_captured = on_captured

            def on_press(key: object) -> None:
                name = format_key(key)
                if name is None:
                    return
                callback = self._on_captured
                with self._lock:
                    self._recording = False
                    self._on_captured = None
                    listener = self._capture_listener
                    self._capture_listener = None
                if listener is not None:
                    listener.stop()
                if callback is not None:
                    callback(name)

            self._capture_listener = keyboard.Listener(on_press=on_press)
            self._capture_listener.daemon = True
            self._capture_listener.start()

    def cancel_capture(self) -> None:
        with self._lock:
            self._stop_capture_locked()

    def _stop_capture_locked(self) -> None:
        self._recording = False
        self._on_captured = None
        if self._capture_listener is not None:
            self._capture_listener.stop()
            self._capture_listener = None

    def _key_matches(self, key: object) -> bool:
        if key == self._vk:
            return True
        # Comparação por nome para KeyCode char case-insensitive
        pressed = format_key(key)
        return pressed is not None and pressed == self._hotkey_name

    @property
    def hotkey(self) -> str:
        return self._hotkey_name

    @property
    def recording(self) -> bool:
        with self._lock:
            return self._recording
