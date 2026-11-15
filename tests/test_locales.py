import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / "ui" / "locales"
CODES = ["pt-BR", "en-US", "zh-CN", "de-DE", "es-ES", "ru-RU"]


def _flatten(obj, prefix=""):
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out |= _flatten(v, f"{prefix}{k}.")
    else:
        out.add(prefix[:-1])
    return out


def _load(code):
    return json.loads((LOCALES / f"{code}.json").read_text(encoding="utf-8"))


def test_all_locales_have_same_keys():
    base = _flatten(_load("pt-BR"))
    for code in CODES[1:]:
        keys = _flatten(_load(code))
        assert base - keys == set(), f"{code} sem chaves: {sorted(base - keys)[:10]}"
        assert keys - base == set(), f"{code} com chaves extras: {sorted(keys - base)[:10]}"


def test_html_keys_exist():
    cat = _load("pt-BR")
    keys = _flatten(cat)
    pattern = r'data-i18n(?:-html|-placeholder|-title|-aria)?="([^"]+)"'
    for page in ("index.html", "info.html", "overlay.html"):
        html = (ROOT / "ui" / page).read_text(encoding="utf-8")
        for key in re.findall(pattern, html):
            assert key in keys, f"{page}: chave ausente {key}"


def test_js_literal_keys_exist():
    keys = _flatten(_load("pt-BR"))
    prefixes = {k.split(".")[0] for k in keys}
    for script in ("app.js", "manual.js"):
        src = (ROOT / "ui" / script).read_text(encoding="utf-8")
        for key in re.findall(r'\bt\(\s*"([A-Za-z0-9_.]+)"', src):
            if key.split(".")[0] in prefixes:
                assert key in keys or any(k.startswith(key + ".") for k in keys), f"{script}: {key}"
