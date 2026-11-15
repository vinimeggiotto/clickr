"""Backend de input Windows via Win32 SendInput (ctypes)."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Literal, Optional

from core.keys import name_to_vk

ButtonName = Literal["left", "right", "middle", "x1", "x2"]

# user32 metrics
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

# mouse event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
WHEEL_DELTA = 120
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000

XBUTTON1 = 0x0001
XBUTTON2 = 0x0002

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
MAPVK_VK_TO_VSC = 0

# (down_flags, up_flags, mouseData)
_BUTTON_FLAGS: dict[ButtonName, tuple[int, int, int]] = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, 0),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, 0),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, 0),
    "x1": (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON1),
    "x2": (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON2),
}


ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_SendInput = _user32.SendInput
_SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
_SendInput.restype = wintypes.UINT

_GetCursorPos = _user32.GetCursorPos
_GetCursorPos.argtypes = (ctypes.POINTER(wintypes.POINT),)
_GetCursorPos.restype = wintypes.BOOL

_GetSystemMetrics = _user32.GetSystemMetrics
_GetSystemMetrics.argtypes = (ctypes.c_int,)
_GetSystemMetrics.restype = ctypes.c_int


def _send(inputs: list[INPUT]) -> None:
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    sent = _SendInput(n, arr, ctypes.sizeof(INPUT))
    if sent != n:
        err = ctypes.get_last_error()
        raise OSError(f"SendInput falhou: enviados {sent}/{n}, erro Win32={err}")


def _mouse_input(flags: int, dx: int = 0, dy: int = 0, mouse_data: int = 0) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi = MOUSEINPUT(
        dx=dx,
        dy=dy,
        mouseData=mouse_data,
        dwFlags=flags,
        time=0,
        dwExtraInfo=0,
    )
    return inp


def _resolve_button(button: ButtonName) -> tuple[int, int, int]:
    try:
        return _BUTTON_FLAGS[button]
    except KeyError as exc:
        raise ValueError(f"Botão inválido: {button}") from exc


def get_cursor_pos() -> tuple[int, int]:
    """Retorna a posição atual do cursor em pixels da tela."""
    pt = wintypes.POINT()
    if not _GetCursorPos(ctypes.byref(pt)):
        raise OSError("GetCursorPos falhou")
    return int(pt.x), int(pt.y)


def get_virtual_screen_rect() -> tuple[int, int, int, int]:
    """Retorna (x, y, width, height) da tela virtual (todos os monitores)."""
    vx = _GetSystemMetrics(SM_XVIRTUALSCREEN)
    vy = _GetSystemMetrics(SM_YVIRTUALSCREEN)
    vw = _GetSystemMetrics(SM_CXVIRTUALSCREEN)
    vh = _GetSystemMetrics(SM_CYVIRTUALSCREEN)
    if vw <= 1 or vh <= 1:
        raise OSError("Métricas da tela virtual inválidas")
    return int(vx), int(vy), int(vw), int(vh)


def _to_absolute(x: int, y: int) -> tuple[int, int]:
    """Converte pixels da tela virtual para coordenadas absolutas SendInput (0–65535)."""
    vx, vy, vw, vh = get_virtual_screen_rect()
    abs_x = int(round((x - vx) * 65535 / (vw - 1)))
    abs_y = int(round((y - vy) * 65535 / (vh - 1)))
    return abs_x, abs_y


def move_absolute(x: int, y: int) -> None:
    """Move o cursor para (x, y) em pixels da tela virtual (multi-monitor)."""
    abs_x, abs_y = _to_absolute(x, y)
    flags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    _send([_mouse_input(flags, dx=abs_x, dy=abs_y)])


def button_down(button: ButtonName) -> None:
    down, _, data = _resolve_button(button)
    _send([_mouse_input(down, mouse_data=data)])


def button_up(button: ButtonName) -> None:
    _, up, data = _resolve_button(button)
    _send([_mouse_input(up, mouse_data=data)])


def click(button: ButtonName) -> None:
    """Clique simples no cursor atual (down + up)."""
    down, up, data = _resolve_button(button)
    _send([_mouse_input(down, mouse_data=data), _mouse_input(up, mouse_data=data)])


_MOVE_FLAGS = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK


def click_at(button: ButtonName, x: int, y: int, restore: bool = False, count: int = 1) -> None:
    """
    Move para (x, y) na tela virtual e clica (ponto fixo / multi-monitor).

    restore=True devolve o cursor à posição original no mesmo lote SendInput.
    """
    abs_x, abs_y = _to_absolute(x, y)
    down, up, data = _resolve_button(button)
    batch = [_mouse_input(_MOVE_FLAGS, dx=abs_x, dy=abs_y)]
    for _ in range(max(1, int(count))):
        batch.append(_mouse_input(down, mouse_data=data))
        batch.append(_mouse_input(up, mouse_data=data))
    if restore:
        ox, oy = get_cursor_pos()
        back_x, back_y = _to_absolute(ox, oy)
        batch.append(_mouse_input(_MOVE_FLAGS, dx=back_x, dy=back_y))
    _send(batch)


def double_click(button: ButtonName) -> None:
    click(button)
    click(button)


def double_click_at(button: ButtonName, x: int, y: int, restore: bool = False) -> None:
    click_at(button, x, y, restore=restore, count=2)


def scroll(dy: int, dx: int = 0) -> None:
    """Rola a roda do mouse: dy > 0 para cima, dx > 0 para a direita (em "cliques")."""
    batch = []
    if dy:
        batch.append(_mouse_input(MOUSEEVENTF_WHEEL, mouse_data=(int(dy) * WHEEL_DELTA) & 0xFFFFFFFF))
    if dx:
        batch.append(_mouse_input(MOUSEEVENTF_HWHEEL, mouse_data=(int(dx) * WHEEL_DELTA) & 0xFFFFFFFF))
    if batch:
        _send(batch)


# --- Teclado ------------------------------------------------------------

_MapVirtualKeyW = _user32.MapVirtualKeyW
_MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
_MapVirtualKeyW.restype = wintypes.UINT

# Teclas que exigem KEYEVENTF_EXTENDEDKEY (bloco de navegação, lado direito, etc.)
_EXTENDED_VKS = frozenset(
    {
        0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,  # PgUp/PgDn/End/Home/setas
        0x2C, 0x2D, 0x2E,  # PrintScreen/Insert/Delete
        0x5B, 0x5C, 0x5D,  # Win esquerdo/direito, Menu
        0x6F,  # divisão do numpad
        0x90,  # NumLock
        0xA3, 0xA5,  # Ctrl direito, Alt direito
    }
)


def _key_input(vk: int, flags: int = 0) -> INPUT:
    vk = int(vk) & 0xFFFF
    if vk in _EXTENDED_VKS:
        flags |= KEYEVENTF_EXTENDEDKEY
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki = KEYBDINPUT(
        wVk=vk,
        wScan=int(_MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)) & 0xFFFF,
        dwFlags=flags,
        time=0,
        dwExtraInfo=0,
    )
    return inp


def _unicode_input(unit: int, flags: int = 0) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki = KEYBDINPUT(
        wVk=0,
        wScan=int(unit) & 0xFFFF,
        dwFlags=KEYEVENTF_UNICODE | flags,
        time=0,
        dwExtraInfo=0,
    )
    return inp


def _utf16_units(text: str) -> list[int]:
    data = text.encode("utf-16-le")
    return [int.from_bytes(data[i : i + 2], "little") for i in range(0, len(data), 2)]


def key_down(vk: int) -> None:
    _send([_key_input(int(vk))])


def key_up(vk: int) -> None:
    _send([_key_input(int(vk), KEYEVENTF_KEYUP)])


def key_press(vk: int) -> None:
    _send([_key_input(int(vk)), _key_input(int(vk), KEYEVENTF_KEYUP)])


def key_press_name(name: str) -> None:
    key_press(name_to_vk(name))


def key_down_name(name: str) -> None:
    key_down(name_to_vk(name))


def key_up_name(name: str) -> None:
    key_up(name_to_vk(name))


def key_down_char(char: str) -> None:
    """Pressiona um caractere arbitrário (Unicode), independente de layout."""
    _send([_unicode_input(u) for u in _utf16_units(char)])


def key_up_char(char: str) -> None:
    _send([_unicode_input(u, KEYEVENTF_KEYUP) for u in _utf16_units(char)])


def type_text(text: str) -> None:
    """Digita texto Unicode (cada unidade UTF-16 como down + up)."""
    for unit in _utf16_units(text or ""):
        _send([_unicode_input(unit), _unicode_input(unit, KEYEVENTF_KEYUP)])


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
