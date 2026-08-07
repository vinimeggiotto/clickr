"""Backend de input Windows via Win32 SendInput (ctypes)."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Literal, Optional

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
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000

XBUTTON1 = 0x0001
XBUTTON2 = 0x0002

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

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
    abs_x = int((x - vx) * 65535 / (vw - 1))
    abs_y = int((y - vy) * 65535 / (vh - 1))
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


def click_at(button: ButtonName, x: int, y: int) -> None:
    """Move para (x, y) na tela virtual e clica (ponto fixo / multi-monitor)."""
    abs_x, abs_y = _to_absolute(x, y)
    move_flags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    down, up, data = _resolve_button(button)
    _send(
        [
            _mouse_input(move_flags, dx=abs_x, dy=abs_y),
            _mouse_input(down, mouse_data=data),
            _mouse_input(up, mouse_data=data),
        ]
    )


def double_click(button: ButtonName) -> None:
    click(button)
    click(button)


def double_click_at(button: ButtonName, x: int, y: int) -> None:
    click_at(button, x, y)
    click_at(button, x, y)


# --- Teclado ------------------------------------------------------------

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


def name_to_vk(name: str) -> int:
    """Converte nome de tecla (ex: A, F6, SPACE) para virtual-key Win32."""
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


def _key_input(vk: int, flags: int = 0) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki = KEYBDINPUT(
        wVk=vk & 0xFFFF,
        wScan=0,
        dwFlags=flags,
        time=0,
        dwExtraInfo=0,
    )
    return inp


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
