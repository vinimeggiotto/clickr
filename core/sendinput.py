"""
Fachada de input multiplataforma.

API pública estável (get_cursor_pos, move_absolute, click_at, double_click_at,
hold, key_*, virtual screen). Backend:
- Windows: Win32 SendInput (core.sendinput_win32)
- macOS / Linux: pynput (core.sendinput_pynput)
- Testes / sem display: CLICKR_INPUT_BACKEND=null (core.sendinput_null)
"""

from __future__ import annotations

import os
import sys
from typing import Literal

ButtonName = Literal["left", "right", "middle", "x1", "x2"]

if os.environ.get("CLICKR_INPUT_BACKEND", "").strip().lower() == "null":
    from core import sendinput_null as _backend
elif sys.platform == "win32":
    from core import sendinput_win32 as _backend
else:
    from core import sendinput_pynput as _backend

get_cursor_pos = _backend.get_cursor_pos
get_virtual_screen_rect = _backend.get_virtual_screen_rect
move_absolute = _backend.move_absolute
button_down = _backend.button_down
button_up = _backend.button_up
click = _backend.click
click_at = _backend.click_at
double_click = _backend.double_click
double_click_at = _backend.double_click_at
name_to_vk = _backend.name_to_vk
key_down = _backend.key_down
key_up = _backend.key_up
key_press = _backend.key_press
key_press_name = _backend.key_press_name
key_down_name = _backend.key_down_name
key_up_name = _backend.key_up_name
button_from_pynput = _backend.button_from_pynput

__all__ = [
    "ButtonName",
    "get_cursor_pos",
    "get_virtual_screen_rect",
    "move_absolute",
    "button_down",
    "button_up",
    "click",
    "click_at",
    "double_click",
    "double_click_at",
    "name_to_vk",
    "key_down",
    "key_up",
    "key_press",
    "key_press_name",
    "key_down_name",
    "key_up_name",
    "button_from_pynput",
]
