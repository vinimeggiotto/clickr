# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

cat = json.loads(Path("ui/locales/pt-BR.json").read_text(encoding="utf-8"))


def get(obj, key):
    cur = obj
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


html = Path("ui/index.html").read_text(encoding="utf-8")
pattern = r'data-i18n(?:-html|-placeholder|-title|-aria)?="([^"]+)"'
keys = set(re.findall(pattern, html))
missing = [k for k in sorted(keys) if get(cat, k) is None]
print("html keys", len(keys), "missing", missing)
for k in (
    "status.active",
    "macro.recording",
    "manual.guide.welcome.title",
    "tray.show",
    "point.seqCount",
):
    assert get(cat, k) is not None, k
print("ok")
