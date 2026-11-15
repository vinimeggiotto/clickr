"""Descrição de teclas pynput sem importar pynput (duck typing)."""

from __future__ import annotations

import sys
from typing import Any, Optional

from core.keys import normalize_name, vk_to_name


def describe_key(key: object) -> Optional[dict[str, Any]]:
    """
    Converte uma tecla pynput em {"name", "vk"?, "char"?}.

    - name: nome estável para exibir e resolver (F6, A, CTRL L, SPACE...).
    - vk: código virtual Win32 (somente no Windows, onde pynput o fornece).
    - char: caractere imprimível, quando houver.
    Retorna None se a tecla não puder ser identificada.
    """
    win = sys.platform == "win32"
    is_enum = hasattr(key, "name") and hasattr(key, "value")
    if is_enum:
        raw = getattr(key, "name", None)
        if not raw:
            return None
        out: dict[str, Any] = {"name": normalize_name(str(raw))}
        vk = getattr(getattr(key, "value", None), "vk", None)
        if win and isinstance(vk, int):
            out["vk"] = vk
        return out

    char = getattr(key, "char", None)
    vk = getattr(key, "vk", None)
    printable = isinstance(char, str) and len(char) == 1 and char.isprintable() and not char.isspace()
    name: Optional[str] = None
    if printable:
        name = char.upper()
    if win and isinstance(vk, int):
        name = vk_to_name(vk) or name or f"VK{vk}"
    elif name is None and isinstance(vk, int) and 0x70 <= vk <= 0x7B:
        name = f"F{vk - 0x6F}"
    if name is None:
        return None
    out = {"name": name}
    if win and isinstance(vk, int):
        out["vk"] = vk
    if printable:
        out["char"] = char
    return out


def format_key(key: object) -> Optional[str]:
    """Nome estável da tecla (ex: F6, A, SPACE), ou None."""
    info = describe_key(key)
    return info["name"] if info else None
