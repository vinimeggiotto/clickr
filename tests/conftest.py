"""Configuração dos testes: backend de input nulo e raiz do repo no path."""

import os
import sys
from pathlib import Path

os.environ["CLICKR_INPUT_BACKEND"] = "null"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402


@pytest.fixture()
def null_input():
    from core import sendinput_null

    sendinput_null.reset()
    yield sendinput_null
    sendinput_null.reset()


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def app(tmp_path, monkeypatch, null_input):
    """AppController real com pywebview/pynput de mentira e dados em tmp_path."""
    import fakes

    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    webview = fakes.install_fake_webview()
    fakes.install_fake_pynput()
    for name in [m for m in sys.modules if m.split(".")[0] in ("app", "hotkeys", "macros")]:
        if name not in ("app.paths", "app.fsutil", "app.log"):
            sys.modules.pop(name, None)
    from app.bootstrap import create_app

    window, controller = create_app()
    controller.bootstrap_services()
    controller.test_window = window
    controller.test_webview = webview
    yield controller
    controller.shutdown()
