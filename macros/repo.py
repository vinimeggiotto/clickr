"""Repositório de macros gravadas em user_data_dir()/macros/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.fsutil import atomic_write_json
from app.paths import user_data_dir
from core.errors import ClickrError
from profiles.repo import ProfilesRepo

MACRO_VERSION = 1
MAX_EVENTS = 200_000
_KINDS = frozenset(
    {"mouse_move", "mouse_down", "mouse_up", "mouse_scroll", "key_down", "key_up"}
)


def validate_events(events: Any) -> list[dict[str, Any]]:
    """Confere a estrutura mínima dos eventos; levanta ClickrError se inválida."""
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise ClickrError("macro.invalidFile", "Arquivo de macro inválido")
    out: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict) or event.get("kind") not in _KINDS:
            raise ClickrError("macro.invalidFile", "Arquivo de macro inválido")
        t = event.get("t", 0)
        if isinstance(t, bool) or not isinstance(t, (int, float)) or t < 0:
            raise ClickrError("macro.invalidFile", "Arquivo de macro inválido")
        out.append(dict(event))
    return out


class MacrosRepo:
    """
    Salva, carrega, lista e exclui macros.

    Arquivo: {user_data_dir()}/macros/{nome}.json
    Formato: {"name", "version": 1, "events": [...]}. As regras de nome são as
    mesmas dos perfis.
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = root if root is not None else user_data_dir() / "macros"

    @property
    def root(self) -> Path:
        return self._root

    def list_macros(self) -> list[str]:
        self._root.mkdir(parents=True, exist_ok=True)
        return sorted((p.stem for p in self._root.glob("*.json")), key=str.casefold)

    def exists(self, name: str) -> bool:
        try:
            return self._path_for(ProfilesRepo._validate_name(name)).is_file()
        except ValueError:
            return False

    def save(self, name: str, events: list[dict[str, Any]]) -> str:
        safe = ProfilesRepo.validate_new_name(name)
        if not events:
            raise ClickrError("macro.empty", "Macro vazia — grave eventos antes de salvar.")
        payload = {"name": safe, "version": MACRO_VERSION, "events": validate_events(events)}
        atomic_write_json(self._path_for(safe), payload)
        return safe

    def load(self, name: str) -> list[dict[str, Any]]:
        safe = ProfilesRepo._validate_name(name)
        path = self._path_for(safe)
        if not path.is_file():
            raise ClickrError("macro.notFound", f"Macro não encontrada: {safe}", name=safe)
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise ClickrError("macro.invalidFile", "Arquivo de macro inválido") from exc
        events = data.get("events") if isinstance(data, dict) else data
        return validate_events(events)

    def delete(self, name: str) -> str:
        safe = ProfilesRepo._validate_name(name)
        path = self._path_for(safe)
        if not path.is_file():
            raise ClickrError("macro.notFound", f"Macro não encontrada: {safe}", name=safe)
        path.unlink()
        return safe

    def _path_for(self, name: str) -> Path:
        return self._root / f"{name}.json"
