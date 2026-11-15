"""Backend de hotkeys por listener pynput (macOS / Linux e reserva no Windows)."""

from __future__ import annotations

import sys
import threading
from typing import Any, Callable, Optional

from core.keys import modifier_family, name_to_vk
from hotkeys.combo import Combo
from hotkeys.keynames import describe_key


def key_vk(key: object, listener: Any = None) -> Optional[int]:
    """Código VK canônico de uma tecla pynput (None se não identificável)."""
    info = describe_key(key)
    if info is None and listener is not None:
        # Com Ctrl/Alt pressionado o SO pode entregar um caractere de controle;
        # canonical() devolve a tecla "base".
        try:
            info = describe_key(listener.canonical(key))
        except Exception:
            info = None
    if info is None:
        return None
    if sys.platform == "win32" and isinstance(info.get("vk"), int):
        return info["vk"]
    try:
        return name_to_vk(info["name"])
    except ValueError:
        return None


class PynputHotkeyBackend:
    """
    Observa o teclado e dispara `on_action(nome)` quando um combo é pressionado.

    Não bloqueia a tecla para os outros programas. Ignora auto-repetição: o
    combo dispara uma vez por pressionamento.
    """

    def __init__(self, on_action: Callable[[str], None]) -> None:
        self._on_action = on_action
        self._lock = threading.Lock()
        self._bindings: dict[str, Combo] = {}
        self._listener: Any = None
        self._mods: set = set()
        self._down: set = set()
        self._paused = False

    def start(self) -> None:
        from pynput import keyboard

        with self._lock:
            if self._listener is not None:
                return
            self._mods.clear()
            self._down.clear()
            self._listener = keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release
            )
            self._listener.daemon = True
            self._listener.start()

    def stop(self) -> None:
        with self._lock:
            listener, self._listener = self._listener, None
        if listener is not None:
            listener.stop()

    def apply(self, bindings: dict[str, Combo]) -> dict[str, str]:
        """Define os combos ativos. Retorna {} (este backend nunca recusa)."""
        with self._lock:
            self._bindings = dict(bindings)
        return {}

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        with self._lock:
            self._mods.clear()
            self._down.clear()
        self._paused = False

    def is_pressed(self, combo: Combo) -> bool:
        with self._lock:
            return combo.vk in self._down

    def _on_press(self, key: object) -> None:
        vk = key_vk(key, self._listener)
        if vk is None:
            return
        fired: list[str] = []
        with self._lock:
            family = modifier_family(vk)
            if family is not None:
                self._mods.add(family)
                return
            if vk in self._down:
                return  # auto-repetição
            self._down.add(vk)
            if self._paused:
                return
            mods = frozenset(self._mods)
            fired = [
                action
                for action, combo in self._bindings.items()
                if combo.vk == vk and combo.mods == mods
            ]
        for action in fired:
            self._on_action(action)

    def _on_release(self, key: object) -> None:
        vk = key_vk(key, self._listener)
        if vk is None:
            return
        with self._lock:
            family = modifier_family(vk)
            if family is not None:
                self._mods.discard(family)
            else:
                self._down.discard(vk)
