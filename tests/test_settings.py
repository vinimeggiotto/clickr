import json
import time

from app.settings import DEFAULT_SETTINGS, AppSettings


def test_missing_file_gives_defaults(tmp_path):
    s = AppSettings(tmp_path / "settings.json")
    assert s.get_locale() is None
    assert s.get("hotkeys")["toggle"] == "F6"
    assert set(s.load()) == set(DEFAULT_SETTINGS)


def test_set_locale_persists(tmp_path):
    s = AppSettings(tmp_path / "settings.json")
    s.set_locale("en-US")
    assert AppSettings(tmp_path / "settings.json").get_locale() == "en-US"


def test_legacy_settings_file(tmp_path):
    """settings.json da 1.0.1 tinha só `locale`."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"locale": "de-DE"}), encoding="utf-8")
    s = AppSettings(path)
    assert s.get_locale() == "de-DE"
    assert s.get("always_on_top") is True and s.get("compact_mode") is False
    assert s.get("last_config") is None


def test_corrupt_file_is_tolerated(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{nao é json", encoding="utf-8")
    assert AppSettings(path).get_locale() is None


def test_invalid_values_fall_back(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"locale": "xx", "activation": "zzz", "window_pos": "a", "time_units": {"start_delay": "dias"},
                    "hotkeys": {"toggle": 5}}),
        encoding="utf-8",
    )
    s = AppSettings(path)
    assert s.get("locale") is None and s.get("activation") == "toggle"
    assert s.get("window_pos") is None
    assert s.get("time_units")["start_delay"] == "ms"
    assert s.get("hotkeys")["toggle"] == "F6"


def test_unknown_keys_are_preserved(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"locale": "pt-BR", "futuro": {"a": 1}}), encoding="utf-8")
    AppSettings(path).update({"compact_mode": True})
    assert json.loads(path.read_text(encoding="utf-8"))["futuro"] == {"a": 1}


def test_deferred_save_and_flush(tmp_path):
    path = tmp_path / "settings.json"
    s = AppSettings(path)
    s.update({"last_script": "click"}, defer=True)
    assert not path.exists()
    s.flush()
    assert json.loads(path.read_text(encoding="utf-8"))["last_script"] == "click"
    s.update({"last_script": "move 1 2"}, defer=True)
    time.sleep(0.8)
    assert json.loads(path.read_text(encoding="utf-8"))["last_script"] == "move 1 2"
