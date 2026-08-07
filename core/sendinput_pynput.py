"""Backend de input macOS/Linux via pynput (já em requirements.txt)."""

from __future__ import annotations

import ctypes
import ctypes.util
import sys
from typing import Literal, Optional, Union

from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController

ButtonName = Literal["left", "right", "middle", "x1", "x2"]

_mouse = MouseController()
_keyboard = KeyboardController()

_BUTTON_MAP: dict[ButtonName, Button] = {
    "left": Button.left,
    "right": Button.right,
    "middle": Button.middle,
}

# X1/X2 existem no enum pynput em várias plataformas; se ausentes, erro explícito.
if hasattr(Button, "x1"):
    _BUTTON_MAP["x1"] = Button.x1  # type: ignore[attr-defined]
if hasattr(Button, "x2"):
    _BUTTON_MAP["x2"] = Button.x2  # type: ignore[attr-defined]

# Nomes → códigos VK Win32 (mesma tabela do backend Windows, para API estável).
_VK_SPECIAL: dict[str, int] = {
    "SPACE": 0x20,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "TAB": 0x09,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "BACKSPACE": 0x08,
    "DELETE": 0x2E,
    "INSERT": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PAGEUP": 0x21,
    "PAGE UP": 0x21,
    "PAGEDOWN": 0x22,
    "PAGE DOWN": 0x22,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "SHIFT": 0x10,
    "CTRL": 0x11,
    "CONTROL": 0x11,
    "ALT": 0x12,
    "WIN": 0x5B,
    "LWIN": 0x5B,
    "RWIN": 0x5C,
}

def _super_key() -> Key:
    if hasattr(Key, "cmd"):
        return Key.cmd  # type: ignore[return-value]
    if hasattr(Key, "cmd_l"):
        return Key.cmd_l  # type: ignore[return-value]
    raise OSError("Tecla Super/Cmd indisponível neste backend pynput")


_VK_TO_KEY: dict[int, Union[Key, KeyCode]] = {
    0x20: Key.space,
    0x0D: Key.enter,
    0x09: Key.tab,
    0x1B: Key.esc,
    0x08: Key.backspace,
    0x2E: Key.delete,
    0x2D: Key.insert,
    0x24: Key.home,
    0x23: Key.end,
    0x21: Key.page_up,
    0x22: Key.page_down,
    0x26: Key.up,
    0x28: Key.down,
    0x25: Key.left,
    0x27: Key.right,
    0x10: Key.shift,
    0x11: Key.ctrl,
    0x12: Key.alt,
    0x5B: _super_key(),
    0x5C: getattr(Key, "cmd_r", None) or _super_key(),
}

for _i in range(1, 25):
    _fk = getattr(Key, f"f{_i}", None)
    if _fk is not None:
        _VK_TO_KEY[0x70 + (_i - 1)] = _fk

for _ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
    _VK_TO_KEY[ord(_ch)] = KeyCode.from_char(_ch.lower() if _ch.isalpha() else _ch)


def _resolve_button(button: ButtonName) -> Button:
    btn = _BUTTON_MAP.get(button)
    if btn is None:
        raise OSError(
            f"Botão '{button}' não suportado neste SO/backend pynput "
            "(X1/X2 podem ser limitados fora do Windows)."
        )
    return btn


def get_cursor_pos() -> tuple[int, int]:
    pos = _mouse.position
    return int(pos[0]), int(pos[1])


def get_virtual_screen_rect() -> tuple[int, int, int, int]:
    """Retorna (x, y, width, height) da área de tela utilizável."""
    if sys.platform == "darwin":
        return _virtual_screen_darwin()
    return _virtual_screen_linux()


def _virtual_screen_darwin() -> tuple[int, int, int, int]:
    """União dos displays via Quartz (ctypes, sem dependência nova)."""
    quartz_name = ctypes.util.find_library("Quartz")
    if not quartz_name:
        raise OSError("Biblioteca Quartz não encontrada (necessário para tela virtual no macOS)")

    quartz = ctypes.cdll.LoadLibrary(quartz_name)

    class CGPoint(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

    class CGSize(ctypes.Structure):
        _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]

    class CGRect(ctypes.Structure):
        _fields_ = [("origin", CGPoint), ("size", CGSize)]

    CGDirectDisplayID = ctypes.c_uint32
    max_displays = 32
    active = (CGDirectDisplayID * max_displays)()
    count = ctypes.c_uint32(0)

    quartz.CGGetActiveDisplayList.argtypes = [
        ctypes.c_uint32,
        ctypes.POINTER(CGDirectDisplayID),
        ctypes.POINTER(ctypes.c_uint32),
    ]
    quartz.CGGetActiveDisplayList.restype = ctypes.c_int32
    err = quartz.CGGetActiveDisplayList(max_displays, active, ctypes.byref(count))
    if err != 0 or count.value < 1:
        raise OSError(f"CGGetActiveDisplayList falhou (código={err})")

    quartz.CGDisplayBounds.argtypes = [CGDirectDisplayID]
    quartz.CGDisplayBounds.restype = CGRect

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for i in range(count.value):
        rect = quartz.CGDisplayBounds(active[i])
        x0 = float(rect.origin.x)
        y0 = float(rect.origin.y)
        x1 = x0 + float(rect.size.width)
        y1 = y0 + float(rect.size.height)
        min_x = min(min_x, x0)
        min_y = min(min_y, y0)
        max_x = max(max_x, x1)
        max_y = max(max_y, y1)

    width = int(max_x - min_x)
    height = int(max_y - min_y)
    if width <= 1 or height <= 1:
        raise OSError("Métricas da tela virtual inválidas (macOS)")
    return int(min_x), int(min_y), width, height


def _virtual_screen_linux() -> tuple[int, int, int, int]:
    """Tamanho da tela padrão via Xlib (X11). Wayland não é suportado aqui."""
    x11_name = ctypes.util.find_library("X11")
    if not x11_name:
        raise OSError(
            "libX11 não encontrada. No Linux o Clickr exige sessão X11 "
            "(Wayland: input sintético e métricas de tela são limitados)."
        )
    x11 = ctypes.cdll.LoadLibrary(x11_name)
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay.restype = ctypes.c_int
    x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
    x11.XDefaultScreen.restype = ctypes.c_int
    x11.XDisplayWidth.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XDisplayWidth.restype = ctypes.c_int
    x11.XDisplayHeight.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XDisplayHeight.restype = ctypes.c_int

    display = x11.XOpenDisplay(None)
    if not display:
        raise OSError(
            "XOpenDisplay falhou. Sessão X11 necessária "
            "(Wayland sem XWayland compatível não é suportado nesta versão)."
        )
    try:
        screen = x11.XDefaultScreen(display)
        width = int(x11.XDisplayWidth(display, screen))
        height = int(x11.XDisplayHeight(display, screen))
    finally:
        x11.XCloseDisplay(display)

    if width <= 1 or height <= 1:
        raise OSError("Métricas da tela inválidas (X11)")
    return 0, 0, width, height


def move_absolute(x: int, y: int) -> None:
    _mouse.position = (int(x), int(y))


def button_down(button: ButtonName) -> None:
    _mouse.press(_resolve_button(button))


def button_up(button: ButtonName) -> None:
    _mouse.release(_resolve_button(button))


def click(button: ButtonName) -> None:
    _mouse.click(_resolve_button(button), 1)


def click_at(button: ButtonName, x: int, y: int) -> None:
    move_absolute(x, y)
    click(button)


def double_click(button: ButtonName) -> None:
    _mouse.click(_resolve_button(button), 2)


def double_click_at(button: ButtonName, x: int, y: int) -> None:
    move_absolute(x, y)
    double_click(button)


def name_to_vk(name: str) -> int:
    """Converte nome de tecla para código VK (compatível com a API Windows)."""
    key_name = (name or "").strip().upper()
    if not key_name:
        raise ValueError("Nome de tecla vazio")
    if key_name.startswith("F") and key_name[1:].isdigit():
        n = int(key_name[1:])
        if 1 <= n <= 24:
            return 0x70 + (n - 1)
    if key_name in _VK_SPECIAL:
        return _VK_SPECIAL[key_name]
    if len(key_name) == 1:
        ch = key_name
        if "A" <= ch <= "Z" or "0" <= ch <= "9":
            return ord(ch)
    raise ValueError(f"Tecla não suportada: {name}")


def _vk_to_pynput(vk: int) -> Union[Key, KeyCode]:
    key = _VK_TO_KEY.get(int(vk))
    if key is None:
        raise OSError(f"VK {vk} sem mapeamento pynput neste SO")
    return key


def key_down(vk: int) -> None:
    _keyboard.press(_vk_to_pynput(vk))


def key_up(vk: int) -> None:
    _keyboard.release(_vk_to_pynput(vk))


def key_press(vk: int) -> None:
    key = _vk_to_pynput(vk)
    _keyboard.press(key)
    _keyboard.release(key)


def key_press_name(name: str) -> None:
    key_press(name_to_vk(name))


def key_down_name(name: str) -> None:
    key_down(name_to_vk(name))


def key_up_name(name: str) -> None:
    key_up(name_to_vk(name))


def button_from_pynput(button: object) -> Optional[ButtonName]:
    """Mapeia botão pynput.mouse.Button para ButtonName, ou None se desconhecido."""
    name = getattr(button, "name", None)
    if name is None:
        return None
    mapping = {
        "left": "left",
        "right": "right",
        "middle": "middle",
        "x1": "x1",
        "x2": "x2",
    }
    return mapping.get(str(name).lower())  # type: ignore[return-value]
