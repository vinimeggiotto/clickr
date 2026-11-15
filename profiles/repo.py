"""Repositório de perfis JSON em user_data_dir()/profiles/."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from app.fsutil import atomic_write_json
from app.paths import user_data_dir
from core.errors import ClickrError
from core.types import PROFILE_VERSION

# Primeiro caractere: letra ou dígito (qualquer idioma). Depois: letras, dígitos,
# espaço, _ . - (máx. 64). Todo nome aceito pela 1.0.1 continua aceito.
_NAME_RE = re.compile(r"^[^\W_][\w .-]{0,63}$", re.UNICODE)
_FORBIDDEN_CHARS = set('<>:"/\\|?*')
_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


class ProfilesRepo:
    """
    Salva, carrega, lista, renomeia, exclui, importa e exporta perfis.

    Diretório: {user_data_dir()}/profiles/{nome}.json

    Formatos aceitos na leitura:
    - v2 (atual): {"name", "version": 2, "config": {...}} — só config de clique.
    - v1 (1.0.x): {"name", "config": {...}} ou o dict de config "cru"; pode
      trazer hotkey/always_on_top/compact_mode. Nunca é reescrito ao carregar.
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
        names = [path.stem for path in self._root.glob("*.json")]
        return sorted(names, key=str.casefold)

    def save(self, name: str, config: dict[str, Any], version: int = PROFILE_VERSION) -> str:
        """Grava no formato atual: {"name", "version", "config"}."""
        safe = self.validate_new_name(name)
        document = {"name": safe, "version": int(version), "config": config}
        atomic_write_json(self._path_for(safe), self._export_payload(document))
        return safe

    def load(self, name: str) -> dict[str, Any]:
        return self.load_document(name)["config"]

    def load_document(self, name: str) -> dict[str, Any]:
        """Retorna {"name", "version", "config"}; arquivos sem version são v1."""
        safe = self._validate_name(name)
        path = self._path_for(safe)
        if not path.is_file():
            raise ClickrError("profile.notFound", f"Perfil não encontrado: {safe}", name=safe)
        return self._read_document(path, safe)

    def delete(self, name: str) -> str:
        safe = self._validate_name(name)
        path = self._path_for(safe)
        if not path.is_file():
            raise ClickrError("profile.notFound", f"Perfil não encontrado: {safe}", name=safe)
        path.unlink()
        return safe

    def rename(self, old: str, new: str) -> str:
        src_name = self._validate_name(old)
        dst_name = self.validate_new_name(new)
        src = self._path_for(src_name)
        if not src.is_file():
            raise ClickrError(
                "profile.notFound", f"Perfil não encontrado: {src_name}", name=src_name
            )
        dst = self._path_for(dst_name)
        if src_name.casefold() != dst_name.casefold() and dst.exists():
            raise ClickrError(
                "profile.exists", f"Já existe um perfil chamado {dst_name}", name=dst_name
            )
        document = self._read_raw(src)
        if isinstance(document, dict) and "config" in document:
            document["name"] = dst_name
        atomic_write_json(dst, document)
        if src != dst:
            try:
                same = src.samefile(dst)
            except OSError:
                same = False
            if not same:
                src.unlink()
        return dst_name

    def export_to(self, name: str, dest: Path) -> Path:
        """Exporta o perfil salvo para um arquivo JSON arbitrário."""
        safe = self._validate_name(name)
        src = self._path_for(safe)
        if not src.is_file():
            raise ClickrError("profile.notFound", f"Perfil não encontrado: {safe}", name=safe)
        document = self._read_document(src, safe)
        document["name"] = safe
        atomic_write_json(Path(dest), self._export_payload(document))
        return Path(dest)

    def export_config(self, name: str, config: dict[str, Any], dest: Path) -> Path:
        """Exporta a configuração atual (não precisa estar salva) para JSON."""
        safe = self._validate_name(name)
        document = {"name": safe, "version": PROFILE_VERSION, "config": config}
        atomic_write_json(Path(dest), self._export_payload(document))
        return Path(dest)

    def import_from(self, src: Path, name: Optional[str] = None) -> str:
        """
        Importa JSON externo para a pasta de perfis, preservando o conteúdo.

        Usa `name` se informado; senão o `name` do arquivo; senão o stem do path.
        """
        src = Path(src)
        if not src.is_file():
            raise ClickrError("profile.fileNotFound", f"Arquivo não encontrado: {src}", path=str(src))
        safe = self.resolve_import_name(src, name)
        document = self._read_document(src, safe)
        document["name"] = safe
        atomic_write_json(self._path_for(safe), self._export_payload(document))
        return safe

    def resolve_import_name(self, src: Path, name: Optional[str] = None) -> str:
        """Nome que import_from usará para o arquivo (sem gravar nada)."""
        src = Path(src)
        raw = self._read_raw(src)
        if name:
            return self.validate_new_name(name)
        if isinstance(raw, dict) and isinstance(raw.get("name"), str) and raw["name"].strip():
            return self.validate_new_name(raw["name"])
        return self.validate_new_name(src.stem)

    def exists(self, name: str) -> bool:
        try:
            safe = self._validate_name(name)
        except ValueError:
            return False
        return self._path_for(safe).is_file()

    def _path_for(self, name: str) -> Path:
        return self._root / f"{name}.json"

    @staticmethod
    def _export_payload(document: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": document["name"]}
        if document.get("version", 1) != 1:
            payload["version"] = document["version"]
        payload["config"] = document["config"]
        return payload

    @staticmethod
    def _read_raw(path: Path) -> Any:
        try:
            return json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise ClickrError("profile.invalidFile", "Arquivo de perfil inválido") from exc

    @classmethod
    def _read_document(cls, path: Path, name: str) -> dict[str, Any]:
        data = cls._read_raw(path)
        if not isinstance(data, dict):
            raise ClickrError("profile.invalidFile", "Arquivo de perfil inválido")
        has_envelope = isinstance(data.get("config"), dict)
        config = data["config"] if has_envelope else data
        if not isinstance(config, dict) or ("config" in data and not has_envelope):
            raise ClickrError("profile.invalidFile", "Configuração de perfil inválida")
        version = data.get("version", 1) if has_envelope else 1
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            version = 1
        return {"name": name, "version": version, "config": config}

    @classmethod
    def _read_config_file(cls, path: Path) -> dict[str, Any]:
        return cls._read_document(path, Path(path).stem)["config"]

    @staticmethod
    def _validate_name(name: str) -> str:
        """Validação usada para ler/apagar: formato do nome, sem lista de reservados."""
        cleaned = (name or "").strip()
        if not _NAME_RE.match(cleaned) or (_FORBIDDEN_CHARS & set(cleaned)):
            raise ClickrError(
                "profile.invalidName",
                "Nome de perfil inválido. Use letras, números, espaço, _ . - (máx. 64).",
            )
        return cleaned

    @classmethod
    def validate_new_name(cls, name: str) -> str:
        """Validação para gravar: formato + nomes reservados do Windows."""
        cleaned = cls._validate_name(name)
        if cleaned.split(".", 1)[0].strip().upper() in _RESERVED:
            raise ClickrError(
                "profile.reservedName",
                f"'{cleaned}' é um nome reservado pelo sistema. Escolha outro.",
                name=cleaned,
            )
        return cleaned
