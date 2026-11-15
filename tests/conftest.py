"""Configuração dos testes: backend de input nulo e raiz do repo no path."""

import os
import sys
from pathlib import Path

os.environ["CLICKR_INPUT_BACKEND"] = "null"

ROOT = Path(__file__).resolve().parent.parent
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
