"""Tabela de teclas: nome estável <-> código virtual (VK no padrão Win32).

Módulo puro (sem dependência de SO) usado pelos backends de input, macros,
scripts e hotkeys. Os códigos seguem a numeração de virtual-key do Windows e
servem como identificador canônico em todas as plataformas.
"""

from __future__ import annotations

from typing import Optional

_VK_NAMED: dict[str, int] = {
    "BACKSPACE": 0x08,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "SHIFT": 0x10,
    "CTRL": 0x11,
    "CONTROL": 0x11,
    "ALT": 0x12,
    "PAUSE": 0x13,
    "CAPS LOCK": 0x14,
    "CAPSLOCK": 0x14,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "SPACE": 0x20,
    "PAGE UP": 0x21,
    "PAGEUP": 0x21,
    "PAGE DOWN": 0x22,
    "PAGEDOWN": 0x22,
    "END": 0x23,
    "HOME": 0x24,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "PRINT SCREEN": 0x2C,
    "PRINTSCREEN": 0x2C,
    "INSERT": 0x2D,
    "DELETE": 0x2E,
    "WIN": 0x5B,
    "LWIN": 0x5B,
    "CMD": 0x5B,
    "CMD L": 0x5B,
    "SUPER": 0x5B,
    "RWIN": 0x5C,
    "CMD R": 0x5C,
    "MENU": 0x5D,
    "NUM LOCK": 0x90,
    "NUMLOCK": 0x90,
    "SCROLL LOCK": 0x91,
    "SCROLLLOCK": 0x91,
    "LSHIFT": 0xA0,
    "SHIFT L": 0xA0,
    "RSHIFT": 0xA1,
    "SHIFT R": 0xA1,
    "LCTRL": 0xA2,
    "CTRL L": 0xA2,
    "RCTRL": 0xA3,
    "CTRL R": 0xA3,
    "LALT": 0xA4,
    "ALT L": 0xA4,
    "RALT": 0xA5,
    "ALT R": 0xA5,
    "ALT GR": 0xA5,
    "ALTGR": 0xA5,
    # Pontuação (posições OEM do layout US)
    ";": 0xBA,
    "=": 0xBB,
    ",": 0xBC,
    "-": 0xBD,
    ".": 0xBE,
    "/": 0xBF,
    "`": 0xC0,
    "[": 0xDB,
    "\\": 0xDC,
    "]": 0xDD,
    "'": 0xDE,
    # Teclado numérico
    "NUM*": 0x6A,
    "NUM+": 0x6B,
    "NUM-": 0x6D,
    "NUM.": 0x6E,
    "NUM/": 0x6F,
}
for _i in range(10):
    _VK_NAMED[f"NUM{_i}"] = 0x60 + _i

# Nome preferido para exibir cada código (primeiro alias "bonito").
_PREFERRED: dict[int, str] = {
    0x08: "BACKSPACE", 0x09: "TAB", 0x0D: "ENTER", 0x10: "SHIFT", 0x11: "CTRL",
    0x12: "ALT", 0x13: "PAUSE", 0x14: "CAPS LOCK", 0x1B: "ESC", 0x20: "SPACE",
    0x21: "PAGE UP", 0x22: "PAGE DOWN", 0x23: "END", 0x24: "HOME", 0x25: "LEFT",
    0x26: "UP", 0x27: "RIGHT", 0x28: "DOWN", 0x2C: "PRINT SCREEN", 0x2D: "INSERT",
    0x2E: "DELETE", 0x5B: "WIN", 0x5C: "RWIN", 0x5D: "MENU", 0x90: "NUM LOCK",
    0x91: "SCROLL LOCK", 0xA0: "LSHIFT", 0xA1: "RSHIFT", 0xA2: "LCTRL",
    0xA3: "RCTRL", 0xA4: "LALT", 0xA5: "RALT",
}

MODIFIER_VKS = frozenset({0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5})


def normalize_name(name: str) -> str:
    return " ".join((name or "").strip().upper().replace("_", " ").split())


def name_to_vk(name: str) -> int:
    """Converte nome de tecla (ex: A, F6, SPACE, CTRL L, ;) para código VK."""
    key_name = normalize_name(name)
    if not key_name:
        raise ValueError("Nome de tecla vazio")
    if key_name[0] == "F" and key_name[1:].isdigit():
        n = int(key_name[1:])
        if 1 <= n <= 24:
            return 0x70 + (n - 1)
    if key_name in _VK_NAMED:
        return _VK_NAMED[key_name]
    if len(key_name) == 1 and ("A" <= key_name <= "Z" or "0" <= key_name <= "9"):
        return ord(key_name)
    raise ValueError(f"Tecla não suportada: {name}")


def vk_to_name(vk: int) -> Optional[str]:
    """Nome estável para um código VK, ou None se desconhecido."""
    vk = int(vk)
    if 0x70 <= vk <= 0x87:
        return f"F{vk - 0x6F}"
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A:
        return chr(vk)
    if vk in _PREFERRED:
        return _PREFERRED[vk]
    for name, code in _VK_NAMED.items():
        if code == vk:
            return name
    return None


def is_modifier_vk(vk: int) -> bool:
    return int(vk) in MODIFIER_VKS


_MOD_FAMILY = {
    0x10: "SHIFT", 0xA0: "SHIFT", 0xA1: "SHIFT",
    0x11: "CTRL", 0xA2: "CTRL", 0xA3: "CTRL",
    0x12: "ALT", 0xA4: "ALT", 0xA5: "ALT",
    0x5B: "WIN", 0x5C: "WIN",
}


def modifier_family(vk: int) -> Optional[str]:
    """CTRL / ALT / SHIFT / WIN para qualquer variante (esq./dir.) do modificador."""
    return _MOD_FAMILY.get(int(vk))


def parse_key_sequence(text: str) -> tuple:
    """
    'E' ou 'CTRL+SHIFT+A' → códigos VK na ordem de pressionamento.

    Diferente de um atalho, aqui cada parte é uma tecla a pressionar de verdade
    (modificadores incluídos). ValueError se alguma parte for inválida.
    """
    pieces: list = []
    for piece in (text or "").split("+"):
        piece = piece.strip()
        if piece == "" and pieces:
            pieces[-1] += "+"  # ex.: NUM+
        elif piece == "":
            raise ValueError("combinação vazia")
        else:
            pieces.append(piece)
    if not pieces:
        raise ValueError("combinação vazia")
    return tuple(name_to_vk(piece) for piece in pieces)
