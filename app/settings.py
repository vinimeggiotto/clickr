"""Preferências do app em user_data_dir()/settings.json.

Guarda tudo o que pertence ao aplicativo e não a um perfil de clique: idioma,
atalhos, opções de janela, última configuração usada, último script etc.
Arquivos antigos (só `locale`) continuam válidos: chaves ausentes assumem o
valor padrão e chaves desconhecidas são preservadas ao gravar.
"""

from __future__ import annotations

import copy
import json
import threading
from pathlib import Path
from typing import Any, Optional

from app.fsutil import atomic_write_json
from app.log import get_logger
from app.paths import user_data_dir

log = get_logger()

SUPPORTED_LOCALES = (
    "pt-BR",
    "en-US",
    "zh-CN",
    "de-DE",
    "es-ES",
    "ru-RU",
)

HOTKEY_ACTIONS = ("toggle", "stop_all", "pick_point", "macro_record")
ACTIVATION_MODES = ("toggle", "hold")
TIME_UNITS = ("ms", "s", "min", "h")
TIME_UNIT_FIELDS = ("start_delay", "max_duration", "burst_pause")

DEFAULT_SETTINGS: dict[str, Any] = {
    "locale": None,
    "hotkeys": {"toggle": "F6", "stop_all": "", "pick_point": "", "macro_record": ""},
    "activation": "toggle",
    "always_on_top": True,
    "compact_mode": False,
    "last_config": None,
    "last_script": "",
    "window_pos": None,
    "manual_seen": False,
    "tray_hint_shown": False,
    "time_units": {"start_delay": "ms", "max_duration": "ms", "burst_pause": "ms"},
    "launch_at_login": False,
    "check_updates": False,
    "schedule": None,
    "macro": {"repeat": 1, "speed": 1.0, "name": ""},
}

MAX_MACRO_REPEAT = 100_000
MIN_MACRO_SPEED = 0.1
MAX_MACRO_SPEED = 10.0
_MAX_SCRIPT_CHARS = 100_000
_SAVE_DEBOUNCE_S = 0.5


def _clean(key: str, value: Any) -> Any:
    """Normaliza um valor; devolve o padrão quando o tipo/conteúdo é inválido."""
    default = copy.deepcopy(DEFAULT_SETTINGS[key])
    if key == "locale":
        return value if isinstance(value, str) and value in SUPPORTED_LOCALES else None
    if key == "hotkeys":
        out = dict(default)
        if isinstance(value, dict):
            for action in HOTKEY_ACTIONS:
                combo = value.get(action)
                if isinstance(combo, str):
                    out[action] = combo.strip().upper()
        return out
    if key == "activation":
        return value if value in ACTIVATION_MODES else default
    if key in ("always_on_top", "compact_mode", "manual_seen", "tray_hint_shown",
               "launch_at_login", "check_updates"):
        return bool(value) if isinstance(value, (bool, int)) else default
    if key == "last_config":
        return copy.deepcopy(value) if isinstance(value, dict) else None
    if key == "last_script":
        return value[:_MAX_SCRIPT_CHARS] if isinstance(value, str) else ""
    if key == "window_pos":
        if (
            isinstance(value, (list, tuple))
            and len(value) == 2
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
        ):
            return [int(value[0]), int(value[1])]
        return None
    if key == "time_units":
        out = dict(default)
        if isinstance(value, dict):
            for field in TIME_UNIT_FIELDS:
                if value.get(field) in TIME_UNITS:
                    out[field] = value[field]
        return out
    if key == "macro":
        out = dict(default)
        if isinstance(value, dict):
            repeat, speed, name = value.get("repeat"), value.get("speed"), value.get("name")
            if isinstance(repeat, int) and not isinstance(repeat, bool):
                out["repeat"] = min(MAX_MACRO_REPEAT, max(1, repeat))
            if isinstance(speed, (int, float)) and not isinstance(speed, bool):
                out["speed"] = min(MAX_MACRO_SPEED, max(MIN_MACRO_SPEED, float(speed)))
            if isinstance(name, str):
                out["name"] = name[:64]
        return out
    if key == "schedule":
        return copy.deepcopy(value) if isinstance(value, dict) else None
    return default


class AppSettings:
    """
    Carrega e grava preferências do aplicativo.

    Arquivo: {user_data_dir()}/settings.json
    Mantém uma cópia em memória; `update(..., defer=True)` agrupa gravações
    frequentes (ex.: última configuração) em uma escrita atômica com atraso.
    """

    def __init__(self, path: Path | None = None) -> None:
        if path is not None:
            self._path = path
        else:
            self._path = user_data_dir() / "settings.json"
        self._lock = threading.RLock()
        self._timer: Optional[threading.Timer] = None
        self._extra: dict[str, Any] = {}
        self._data: dict[str, Any] = copy.deepcopy(DEFAULT_SETTINGS)
        self._read()

    @property
    def path(self) -> Path:
        return self._path

    def ensure_dir(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> None:
        raw: Any = None
        if self._path.is_file():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError, UnicodeError):
                log.warning("settings.json ilegível; usando padrões")
        if not isinstance(raw, dict):
            raw = {}
        with self._lock:
            self._data = {
                key: _clean(key, raw[key]) if key in raw else copy.deepcopy(default)
                for key, default in DEFAULT_SETTINGS.items()
            }
            self._extra = {k: v for k, v in raw.items() if k not in DEFAULT_SETTINGS}

    def load(self) -> dict[str, Any]:
        """Cópia das preferências atuais (todas as chaves conhecidas)."""
        with self._lock:
            return copy.deepcopy(self._data)

    def get(self, key: str) -> Any:
        with self._lock:
            return copy.deepcopy(self._data[key])

    def update(self, values: dict[str, Any], defer: bool = False) -> dict[str, Any]:
        """Aplica valores normalizados; grava já ou, com defer, após um curto atraso."""
        with self._lock:
            for key, value in values.items():
                if key in DEFAULT_SETTINGS:
                    self._data[key] = _clean(key, value)
            snapshot = copy.deepcopy(self._data)
            if defer:
                if self._timer is None:
                    self._timer = threading.Timer(_SAVE_DEBOUNCE_S, self.flush)
                    self._timer.daemon = True
                    self._timer.start()
            else:
                self._write_locked()
        return snapshot

    def save(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Compatibilidade: grava os valores informados e devolve o resultado."""
        return self.update(settings)

    def flush(self) -> None:
        """Grava agora o que estiver pendente."""
        with self._lock:
            self._write_locked()

    def _write_locked(self) -> None:
        timer, self._timer = self._timer, None
        if timer is not None:
            timer.cancel()
        payload = dict(self._extra)
        payload.update(copy.deepcopy(self._data))
        try:
            atomic_write_json(self._path, payload)
        except OSError:
            log.exception("Falha ao gravar settings.json")

    def get_locale(self) -> Optional[str]:
        return self.get("locale")

    def set_locale(self, code: str) -> dict[str, Any]:
        if code not in SUPPORTED_LOCALES:
            raise ValueError(f"Locale não suportado: {code}")
        return self.update({"locale": code})
