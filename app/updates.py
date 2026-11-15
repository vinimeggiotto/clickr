"""Verificação opcional de nova versão no GitHub Releases.

Só roda quando o usuário liga a opção. A requisição é um GET anônimo à API
pública de releases do projeto: não envia nenhum dado do usuário nem da máquina.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any, Callable, Optional

REPO = "vinimeggiotto/clickr"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
_TIMEOUT_S = 6


def parse_version(text: str) -> tuple[int, ...]:
    """'v1.2.3' / '1.2' → (1, 2, 3) / (1, 2). Trechos não numéricos são ignorados."""
    numbers = re.findall(r"\d+", str(text or "").split("-", 1)[0])
    return tuple(int(n) for n in numbers[:4])


def is_newer(candidate: str, current: str) -> bool:
    a, b = parse_version(candidate), parse_version(current)
    if not a or not b:
        return False
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))


def _fetch_latest() -> dict[str, Any]:
    request = urllib.request.Request(
        RELEASES_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Clickr-update-check"},
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT_S) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def safe_release_url(url: Any) -> str:
    """Só aceita links da página de releases do próprio projeto."""
    text = str(url or "")
    return text if text.startswith(RELEASES_PAGE) else RELEASES_PAGE


def check_latest(
    current_version: str, fetch: Callable[[], dict[str, Any]] = _fetch_latest
) -> Optional[dict[str, str]]:
    """
    Retorna {"version", "url"} se houver release mais nova que `current_version`,
    senão None. Erros de rede ou resposta inesperada levantam OSError/ValueError.
    """
    data = fetch()
    if not isinstance(data, dict):
        raise ValueError("Resposta inesperada do GitHub")
    if data.get("draft") or data.get("prerelease"):
        return None
    tag = str(data.get("tag_name") or "")
    if not is_newer(tag, current_version):
        return None
    return {"version": tag.lstrip("vV"), "url": safe_release_url(data.get("html_url"))}
