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

from core.keys import name_to_vk

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

def _super_key() -> Key:
    if hasattr(Key, "cmd"):
        return Key.cmd  # type: ignore[return-value]
    if hasattr(Key, "cmd_l"):
        return Key.cmd_l  # type: ignore[return-value]
    raise OSError("Tecla Super/Cmd indisponível neste backend pynput")


def _key(*names: str) -> Optional[Key]:
    """Primeiro membro existente de pynput.keyboard.Key entre os nomes dados."""
    for name in names:
        member = getattr(Key, name, None)
        if member is not None:
            return member
    return None


_VK_TO_KEY: dict[int, Union[Key, KeyCode]] = {}
for _vk, _names in {
    0x08: ("backspace",),
    0x09: ("tab",),
    0x0D: ("enter",),
    0x10: ("shift",),
    0x11: ("ctrl",),
    0x12: ("alt",),
    0x13: ("pause",),
    0x14: ("caps_lock",),
    0x1B: ("esc",),
    0x20: ("space",),
    0x21: ("page_up",),
    0x22: ("page_down",),
    0x23: ("end",),
    0x24: ("home",),
    0x25: ("left",),
    0x26: ("up",),
    0x27: ("right",),
    0x28: ("down",),
    0x2C: ("print_screen",),
    0x2D: ("insert",),
    0x2E: ("delete",),
    0x5B: ("cmd", "cmd_l"),
    0x5C: ("cmd_r", "cmd"),
    0x5D: ("menu",),
    0x90: ("num_lock",),
    0x91: ("scroll_lock",),
    0xA0: ("shift_l", "shift"),
    0xA1: ("shift_r", "shift"),
    0xA2: ("ctrl_l", "ctrl"),
    0xA3: ("ctrl_r", "ctrl"),
    0xA4: ("alt_l", "alt"),
    0xA5: ("alt_gr", "alt_r", "alt"),
}.items():
    _member = _key(*_names)
    if _member is not None:
        _VK_TO_KEY[_vk] = _member

for _i in range(1, 25):
    _fk = getattr(Key, f"f{_i}", None)
    if _fk is not None:
        _VK_TO_KEY[0x70 + (_i - 1)] = _fk

for _ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
    _VK_TO_KEY[ord(_ch)] = KeyCode.from_char(_ch.lower() if _ch.isalpha() else _ch)

for _vk, _ch in {
    0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".", 0xBF: "/", 0xC0: "`",
    0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'",
    0x6A: "*", 0x6B: "+", 0x6D: "-", 0x6E: ".", 0x6F: "/",
}.items():
    _VK_TO_KEY[_vk] = KeyCode.from_char(_ch)

for _i in range(10):
    _VK_TO_KEY[0x60 + _i] = KeyCode.from_char(str(_i))


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


def click_at(button: ButtonName, x: int, y: int, restore: bool = False, count: int = 1) -> None:
    origin = _mouse.position if restore else None
    move_absolute(x, y)
    _mouse.click(_resolve_button(button), max(1, int(count)))
    if origin is not None:
        _mouse.position = (int(origin[0]), int(origin[1]))


def double_click(button: ButtonName) -> None:
    _mouse.click(_resolve_button(button), 2)


def double_click_at(button: ButtonName, x: int, y: int, restore: bool = False) -> None:
    click_at(button, x, y, restore=restore, count=2)


def scroll(dy: int, dx: int = 0) -> None:
    """Rola a roda do mouse: dy > 0 para cima, dx > 0 para a direita."""
    if dy or dx:
        _mouse.scroll(int(dx), int(dy))


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


def key_down_char(char: str) -> None:
    _keyboard.press(KeyCode.from_char(char))


def key_up_char(char: str) -> None:
    _keyboard.release(KeyCode.from_char(char))


def type_text(text: str) -> None:
    _keyboard.type(text or "")


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
