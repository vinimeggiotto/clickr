import json

import pytest

from core.types import ClickConfig
from profiles.repo import ProfilesRepo


def test_save_load_list(tmp_path):
    repo = ProfilesRepo(tmp_path)
    repo.save("meu-preset", ClickConfig(interval_ms=42).to_dict())
    assert repo.list_profiles() == ["meu-preset"]
    assert repo.load("meu-preset")["interval_ms"] == 42


def test_invalid_name(tmp_path):
    repo = ProfilesRepo(tmp_path)
    with pytest.raises(ValueError):
        repo.save("../fora", {})
    with pytest.raises(ValueError):
        repo.save("", {})


def test_legacy_envelope_profile_loads(tmp_path, fixtures_dir):
    repo = ProfilesRepo(tmp_path)
    name = repo.import_from(fixtures_dir / "profile_v1_envelope.json")
    assert name == "farm-legado"
    data = repo.load(name)
    cfg = ClickConfig.from_dict(data)
    assert cfg.interval_ms == 150
    assert cfg.button == "right"
    assert cfg.click_type == "double"
    assert cfg.position_mode == "fixed"
    assert (cfg.fixed_x, cfg.fixed_y) == (640, 360)
    assert cfg.burst_count == 3 and cfg.burst_pause_ms == 250
    assert len(cfg.sequence) == 2
    assert cfg.window_filter.enabled and cfg.window_filter.process == "notepad.exe"


def test_legacy_raw_profile_loads(tmp_path, fixtures_dir):
    repo = ProfilesRepo(tmp_path)
    name = repo.import_from(fixtures_dir / "profile_v1_raw.json")
    assert name == "profile_v1_raw"
    cfg = ClickConfig.from_dict(repo.load(name))
    assert cfg.interval_ms == 33
    assert cfg.button == "middle"
    assert cfg.click_type == "hold"


def test_legacy_file_placed_directly_in_folder(tmp_path, fixtures_dir):
    """Perfil 1.0.1 já existente em profiles/ deve carregar sem migração."""
    raw = (fixtures_dir / "profile_v1_envelope.json").read_text(encoding="utf-8")
    (tmp_path / "antigo.json").write_text(raw, encoding="utf-8")
    repo = ProfilesRepo(tmp_path)
    assert "antigo" in repo.list_profiles()
    assert repo.load("antigo")["interval_ms"] == 150
    # A carga não reescreve o arquivo legado.
    assert json.loads((tmp_path / "antigo.json").read_text(encoding="utf-8")) == json.loads(raw)


def test_unicode_names_accepted(tmp_path):
    repo = ProfilesRepo(tmp_path)
    for name in ["Configuração", "ação rápida", "プロファイル1", "meu-preset", "a.b_c 1"]:
        assert repo.save(name, {}) == name
    assert set(repo.list_profiles()) >= {"Configuração", "meu-preset"}


@pytest.mark.parametrize("name", ["CON", "nul", "COM1", "LPT9.backup", "a/b", "a\\b", "x:y", "_a", " "])
def test_bad_new_names_rejected(tmp_path, name):
    with pytest.raises(ValueError):
        ProfilesRepo(tmp_path).save(name, {})


def test_delete_and_rename(tmp_path):
    repo = ProfilesRepo(tmp_path)
    repo.save("a", {"interval_ms": 5})
    repo.save("b", {})
    assert repo.rename("a", "c") == "c"
    assert repo.list_profiles() == ["b", "c"]
    assert repo.load("c")["interval_ms"] == 5
    with pytest.raises(ValueError):
        repo.rename("c", "b")
    repo.delete("b")
    assert repo.list_profiles() == ["c"]
    with pytest.raises(ValueError):
        repo.delete("b")


def test_no_temp_files_left(tmp_path):
    repo = ProfilesRepo(tmp_path)
    repo.save("x", {})
    assert [p.name for p in tmp_path.iterdir()] == ["x.json"]


def test_import_preserves_legacy_app_keys(tmp_path, fixtures_dir):
    repo = ProfilesRepo(tmp_path)
    repo.import_from(fixtures_dir / "profile_v1_envelope.json")
    doc = repo.load_document("farm-legado")
    assert doc["version"] == 1
    assert doc["config"]["hotkey"] == "F8"
