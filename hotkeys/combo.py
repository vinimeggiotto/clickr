"""Combinações de teclas: 'CTRL+ALT+F6' <-> Combo (módulo puro)."""

from __future__ import annotations

from dataclasses import dataclass

from core.keys import is_modifier_vk, name_to_vk, normalize_name, vk_to_name

MODS = ("CTRL", "ALT", "SHIFT", "WIN")
_MOD_ALIASES = {
    "CTRL": "CTRL", "CONTROL": "CTRL", "LCTRL": "CTRL", "RCTRL": "CTRL",
    "ALT": "ALT", "LALT": "ALT", "RALT": "ALT", "ALTGR": "ALT", "ALT GR": "ALT",
    "SHIFT": "SHIFT", "LSHIFT": "SHIFT", "RSHIFT": "SHIFT",
    "WIN": "WIN", "LWIN": "WIN", "RWIN": "WIN", "CMD": "WIN", "SUPER": "WIN", "META": "WIN",
}


@dataclass(frozen=True)
class Combo:
    """Modificadores (famílias CTRL/ALT/SHIFT/WIN) + uma tecla principal."""

    mods: frozenset
    vk: int
    key: str

    def __str__(self) -> str:
        return "+".join([m for m in MODS if m in self.mods] + [self.key])

    def tokens(self) -> set:
        """Identificadores (família de modificador ou vk) de todas as teclas do combo."""
        return set(self.mods) | {self.vk}


def make_combo(mods: set, vk: int) -> Combo:
    name = vk_to_name(vk) or f"VK{int(vk)}"
    return Combo(mods=frozenset(mods), vk=int(vk), key=name)


def parse_combo(text: str) -> Combo:
    """
    'F6', 'ctrl+alt+f6', 'SHIFT+A' → Combo. ValueError se inválido.

    A última parte é a tecla principal e não pode ser um modificador.
    """
    pieces: list[str] = []
    for piece in normalize_name(text).split("+"):
        piece = piece.strip()
        if piece == "" and pieces:
            pieces[-1] += "+"  # ex.: NUM+
        elif piece == "":
            raise ValueError("Hotkey vazia")
        else:
            pieces.append(piece)
    if not pieces:
        raise ValueError("Hotkey vazia")
    mods: set = set()
    for piece in pieces[:-1]:
        family = _MOD_ALIASES.get(piece)
        if family is None:
            raise ValueError(f"Modificador inválido: {piece}")
        mods.add(family)
    vk = name_to_vk(pieces[-1])
    if is_modifier_vk(vk):
        raise ValueError("A combinação precisa de uma tecla além dos modificadores")
    return make_combo(mods, vk)
