"""Repositório de perfis JSON em user_data_dir()/profiles/."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from app.paths import user_data_dir

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}$")


class ProfilesRepo:
    """
    Salva, carrega, lista, importa e exporta perfis de configuração.

    Diretório: {user_data_dir()}/profiles/{nome}.json
    """

    def __init__(self, root: Path | None = None) -> None:
        if root is not None:
            self._root = root
        else:
            self._root = user_data_dir() / "profiles"

    @property
    def root(self) -> Path:
        return self._root

    def ensure_dir(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> list[str]:
        self.ensure_dir()
        names: list[str] = []
        for path in sorted(self._root.glob("*.json")):
            names.append(path.stem)
        return names

    def save(self, name: str, config: dict[str, Any]) -> str:
        safe = self._validate_name(name)
        self.ensure_dir()
        path = self._path_for(safe)
        payload = {"name": safe, "config": config}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return safe

    def load(self, name: str) -> dict[str, Any]:
        safe = self._validate_name(name)
        path = self._path_for(safe)
        if not path.is_file():
            raise FileNotFoundError(f"Perfil não encontrado: {safe}")
        return self._read_config_file(path)

    def export_to(self, name: str, dest: Path) -> Path:
        """Exporta o perfil salvo para um arquivo JSON arbitrário."""
        safe = self._validate_name(name)
        src = self._path_for(safe)
        if not src.is_file():
            raise FileNotFoundError(f"Perfil não encontrado: {safe}")
        config = self._read_config_file(src)
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload = {"name": safe, "config": config}
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return dest

    def export_config(self, name: str, config: dict[str, Any], dest: Path) -> Path:
        """Exporta a configuração atual (não precisa estar salva) para JSON."""
        safe = self._validate_name(name)
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload = {"name": safe, "config": config}
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return dest

    def import_from(self, src: Path, name: Optional[str] = None) -> str:
        """
        Importa JSON externo para a pasta de perfis.

        Usa `name` se informado; senão o `name` do arquivo; senão o stem do path.
        """
        src = Path(src)
        if not src.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {src}")
        raw = json.loads(src.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Arquivo de perfil inválido")
        config = raw.get("config", raw)
        if not isinstance(config, dict):
            raise ValueError("Configuração de perfil inválida")
        if name:
            safe = self._validate_name(name)
        elif isinstance(raw.get("name"), str) and raw["name"].strip():
            safe = self._validate_name(raw["name"])
        else:
            safe = self._validate_name(src.stem)
        return self.save(safe, config)

    def exists(self, name: str) -> bool:
        try:
            safe = self._validate_name(name)
        except ValueError:
            return False
        return self._path_for(safe).is_file()

    def _path_for(self, name: str) -> Path:
        return self._root / f"{name}.json"

    @staticmethod
    def _read_config_file(path: Path) -> dict[str, Any]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Arquivo de perfil inválido")
        config = data.get("config", data)
        if not isinstance(config, dict):
            raise ValueError("Configuração de perfil inválida")
        return config

    @staticmethod
    def _validate_name(name: str) -> str:
        cleaned = (name or "").strip()
        if not _NAME_RE.match(cleaned):
            raise ValueError(
                "Nome de perfil inválido. Use letras, números, espaço, _ . - (máx. 64)."
            )
        return cleaned
