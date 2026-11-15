"""Preferências do app em user_data_dir()/settings.json (locale da UI)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.fsutil import atomic_write_json
from app.paths import user_data_dir

SUPPORTED_LOCALES = (
    "pt-BR",
    "en-US",
    "zh-CN",
    "de-DE",
    "es-ES",
    "ru-RU",
)

DEFAULT_SETTINGS: dict[str, Any] = {
    "locale": None,
}


class AppSettings:
    """
    Carrega e grava preferências do aplicativo.

    Arquivo: {user_data_dir()}/settings.json
    Não mistura com presets de clique em profiles/.
    """

    def __init__(self, path: Path | None = None) -> None:
        if path is not None:
            self._path = path
        else:
            self._path = user_data_dir() / "settings.json"

    @property
    def path(self) -> Path:
        return self._path

    def ensure_dir(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        """Retorna dict com chaves conhecidas; locale inválido vira None."""
        data = dict(DEFAULT_SETTINGS)
        if not self._path.is_file():
            return data
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return data
        if not isinstance(raw, dict):
            return data
        locale = raw.get("locale")
        if isinstance(locale, str) and locale in SUPPORTED_LOCALES:
            data["locale"] = locale
        else:
            data["locale"] = None
        return data

    def save(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Persiste settings normalizados e devolve o resultado gravado."""
        locale = settings.get("locale")
        payload: dict[str, Any] = {
            "locale": locale if isinstance(locale, str) and locale in SUPPORTED_LOCALES else None,
        }
        atomic_write_json(self._path, payload)
        return dict(payload)

    def get_locale(self) -> Optional[str]:
        return self.load().get("locale")

    def set_locale(self, code: str) -> dict[str, Any]:
        if code not in SUPPORTED_LOCALES:
            raise ValueError(f"Locale não suportado: {code}")
        return self.save({"locale": code})
