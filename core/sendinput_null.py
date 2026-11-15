"""Backend de input nulo: registra as chamadas sem tocar no SO.

Selecionado com a variável de ambiente CLICKR_INPUT_BACKEND=null.
Usado em testes automatizados e em ambientes sem display.
"""

from __future__ import annotations

import threading
from typing import Any, Literal, Optional

from core.keys import name_to_vk

ButtonName = Literal["left", "right", "middle", "x1", "x2"]

_VALID = ("left", "right", "middle", "x1", "x2")
_lock = threading.Lock()
calls: list[tuple[Any, ...]] = []
_cursor = [0, 0]
_virtual_screen = (0, 0, 1920, 1080)


def reset() -> None:
    with _lock:
        calls.clear()
        _cursor[0] = 0
        _cursor[1] = 0


def recorded() -> list[tuple[Any, ...]]:
    with _lock:
        return list(calls)


def _log(*entry: Any) -> None:
    with _lock:
        calls.append(entry)


def _check(button: str) -> None:
    if button not in _VALID:
        raise ValueError(f"Botão inválido: {button}")


def get_cursor_pos() -> tuple[int, int]:
    with _lock:
        return _cursor[0], _cursor[1]


def set_cursor_pos_for_test(x: int, y: int) -> None:
    with _lock:
        _cursor[0], _cursor[1] = int(x), int(y)


def get_virtual_screen_rect() -> tuple[int, int, int, int]:
    return _virtual_screen


def move_absolute(x: int, y: int) -> None:
    with _lock:
        _cursor[0], _cursor[1] = int(x), int(y)
        calls.append(("move", int(x), int(y)))


def button_down(button: ButtonName) -> None:
    _check(button)
    _log("down", button)


def button_up(button: ButtonName) -> None:
    _check(button)
    _log("up", button)


def click(button: ButtonName) -> None:
    _check(button)
    _log("click", button)


def click_at(button: ButtonName, x: int, y: int) -> None:
    _check(button)
    move_absolute(x, y)
    _log("click", button)


def double_click(button: ButtonName) -> None:
    click(button)
    click(button)


def double_click_at(button: ButtonName, x: int, y: int) -> None:
    click_at(button, x, y)
    click_at(button, x, y)


def key_down(vk: int) -> None:
    _log("key_down", int(vk))


def key_up(vk: int) -> None:
    _log("key_up", int(vk))


def key_press(vk: int) -> None:
    key_down(vk)
    key_up(vk)


def key_press_name(name: str) -> None:
    key_press(name_to_vk(name))


def key_down_name(name: str) -> None:
    key_down(name_to_vk(name))


def key_up_name(name: str) -> None:
    key_up(name_to_vk(name))


def button_from_pynput(button: object) -> Optional[ButtonName]:
    name = getattr(button, "name", None)
    if name is None:
        return None
    low = str(name).lower()
    return low if low in _VALID else None  # type: ignore[return-value]
