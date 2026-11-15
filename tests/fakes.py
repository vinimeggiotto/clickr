"""Dublês de pywebview e pynput para testar o controller sem GUI nem display."""

from __future__ import annotations

import enum
import sys
import types
from typing import Any, Callable, Optional


class _Event:
    def __init__(self) -> None:
        self.handlers: list[Callable[..., Any]] = []

    def __iadd__(self, handler: Callable[..., Any]) -> "_Event":
        self.handlers.append(handler)
        return self

    def __isub__(self, handler: Callable[..., Any]) -> "_Event":
        if handler in self.handlers:
            self.handlers.remove(handler)
        return self

    def fire(self, *args: Any) -> list[Any]:
        return [h(*args) for h in list(self.handlers)]


class _Events:
    def __init__(self) -> None:
        self.closed = _Event()
        self.closing = _Event()
        self.moved = _Event()
        self.shown = _Event()
        self.loaded = _Event()


class FakeWindow:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.title = kwargs.get("title", "")
        self.x = kwargs.get("x") or 100
        self.y = kwargs.get("y") or 100
        self.width = kwargs.get("width") or 468
        self.height = kwargs.get("height") or 676
        self.on_top = bool(kwargs.get("on_top", False))
        self.events = _Events()
        self.visible = True
        self.destroyed = False
        self.js: list[str] = []
        self.dialog_result: Any = None

    def evaluate_js(self, code: str) -> None:
        self.js.append(code)
        if len(self.js) > 200:
            del self.js[:100]

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    def restore(self) -> None:
        self.visible = True

    def minimize(self) -> None:
        self.minimized = True

    def move(self, x: int, y: int) -> None:
        self.x, self.y = int(x), int(y)

    def destroy(self) -> None:
        if self.destroyed:
            return
        self.destroyed = True
        self.events.closed.fire()

    def create_file_dialog(self, dialog_type: Any, **kwargs: Any) -> Any:
        return self.dialog_result


def install_fake_webview() -> types.ModuleType:
    module = types.ModuleType("webview")
    module.windows = []  # type: ignore[attr-defined]
    module.SAVE_DIALOG = 30  # type: ignore[attr-defined]
    module.OPEN_DIALOG = 10  # type: ignore[attr-defined]

    def create_window(**kwargs: Any) -> FakeWindow:
        window = FakeWindow(**kwargs)
        module.windows.append(window)  # type: ignore[attr-defined]
        return window

    def create_file_dialog(dialog_type: Any, **kwargs: Any) -> Any:
        return None

    module.create_window = create_window  # type: ignore[attr-defined]
    module.create_file_dialog = create_file_dialog  # type: ignore[attr-defined]
    module.start = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules["webview"] = module
    return module


class _KeyCode:
    def __init__(self, vk: Optional[int] = None, char: Optional[str] = None) -> None:
        self.vk = vk
        self.char = char

    @classmethod
    def from_char(cls, char: str) -> "_KeyCode":
        return cls(char=char)

    @classmethod
    def from_vk(cls, vk: int) -> "_KeyCode":
        return cls(vk=vk)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _KeyCode) and (self.vk, self.char) == (other.vk, other.char)

    def __hash__(self) -> int:
        return hash((self.vk, self.char))


class _Listener:
    instances: list["_Listener"] = []

    def __init__(self, **callbacks: Any) -> None:
        self.callbacks = callbacks
        self.daemon = True
        self.running = False
        _Listener.instances.append(self)

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def emit(self, name: str, *args: Any) -> None:
        callback = self.callbacks.get(name)
        if callback is not None and self.running:
            callback(*args)


def install_fake_pynput() -> types.ModuleType:
    names = (
        ["alt", "alt_l", "alt_r", "alt_gr", "backspace", "caps_lock", "cmd", "cmd_l", "cmd_r",
         "ctrl", "ctrl_l", "ctrl_r", "delete", "down", "end", "enter", "esc", "home", "insert",
         "left", "menu", "num_lock", "page_down", "page_up", "pause", "print_screen", "right",
         "scroll_lock", "shift", "shift_l", "shift_r", "space", "tab", "up"]
        + [f"f{i}" for i in range(1, 25)]
    )
    Key = enum.Enum("Key", {name: _KeyCode(vk=1000 + i) for i, name in enumerate(names)})
    Button = enum.Enum("Button", {"left": 1, "middle": 2, "right": 3, "x1": 4, "x2": 5})

    class KeyboardListener(_Listener):
        pass

    class MouseListener(_Listener):
        pass

    keyboard = types.ModuleType("pynput.keyboard")
    keyboard.Key = Key  # type: ignore[attr-defined]
    keyboard.KeyCode = _KeyCode  # type: ignore[attr-defined]
    keyboard.Listener = KeyboardListener  # type: ignore[attr-defined]
    mouse = types.ModuleType("pynput.mouse")
    mouse.Button = Button  # type: ignore[attr-defined]
    mouse.Listener = MouseListener  # type: ignore[attr-defined]
    pynput = types.ModuleType("pynput")
    pynput.keyboard = keyboard  # type: ignore[attr-defined]
    pynput.mouse = mouse  # type: ignore[attr-defined]
    sys.modules["pynput"] = pynput
    sys.modules["pynput.keyboard"] = keyboard
    sys.modules["pynput.mouse"] = mouse
    _Listener.instances.clear()
    return pynput


def listeners() -> list[_Listener]:
    return list(_Listener.instances)
