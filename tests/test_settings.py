import json

from app.settings import AppSettings


def test_missing_file_gives_defaults(tmp_path):
    s = AppSettings(tmp_path / "settings.json")
    assert s.get_locale() is None


def test_set_locale_persists(tmp_path):
    s = AppSettings(tmp_path / "settings.json")
    s.set_locale("en-US")
    assert AppSettings(tmp_path / "settings.json").get_locale() == "en-US"


def test_legacy_settings_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"locale": "de-DE"}), encoding="utf-8")
    assert AppSettings(path).get_locale() == "de-DE"


def test_corrupt_file_is_tolerated(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{nao é json", encoding="utf-8")
    assert AppSettings(path).get_locale() is None
