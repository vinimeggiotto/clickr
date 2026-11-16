import time

from macros.player import MacroPlayer


def _play(player, events, **kw):
    assert player.play(events, **kw)
    deadline = time.time() + 3
    while player.is_playing() and time.time() < deadline:
        time.sleep(0.005)
    assert not player.is_playing()


def test_modifier_and_punctuation_names_replay(null_input):
    """Nomes gravados pela 1.0.1 (CTRL L, ALT L, ;) não abortam mais."""
    events = [
        {"t": 0.0, "kind": "key_down", "key": "CTRL L"},
        {"t": 0.0, "kind": "key_down", "key": "C"},
        {"t": 0.0, "kind": "key_up", "key": "C"},
        {"t": 0.0, "kind": "key_up", "key": "CTRL L"},
        {"t": 0.0, "kind": "key_down", "key": ";"},
        {"t": 0.0, "kind": "key_up", "key": ";"},
        {"t": 0.0, "kind": "key_down", "key": "CAPS LOCK"},
        {"t": 0.0, "kind": "key_up", "key": "CAPS LOCK"},
    ]
    player = MacroPlayer()
    _play(player, events)
    assert player.last_error() is None
    rec = null_input.recorded()
    assert ("key_down", 0xA2) in rec and ("key_down", ord("C")) in rec
    assert ("key_down", 0xBA) in rec


def test_char_fallback(null_input):
    player = MacroPlayer()
    _play(player, [{"t": 0, "kind": "key_down", "key": "Ç", "char": "ç"},
                   {"t": 0, "kind": "key_up", "key": "Ç", "char": "ç"}])
    assert player.last_error() is None
    assert ("char_down", "ç") in null_input.recorded()


def test_unsupported_key_reports_code(null_input):
    player = MacroPlayer()
    _play(player, [{"t": 0, "kind": "key_down", "key": "???"}])
    assert player.last_error()["code"] == "macro.unsupportedKey"


def test_stop_releases_everything(null_input):
    events = [
        {"t": 0.0, "kind": "key_down", "key": "SHIFT"},
        {"t": 0.0, "kind": "mouse_down", "x": 1, "y": 1, "button": "left"},
        {"t": 5.0, "kind": "key_up", "key": "SHIFT"},
    ]
    player = MacroPlayer()
    assert player.play(events)
    time.sleep(0.1)
    player.stop()
    rec = null_input.recorded()
    assert ("key_up", 0x10) in rec
    assert ("up", "left") in rec


def test_repeat_and_speed(null_input):
    events = [{"t": 0.2, "kind": "mouse_down", "x": 1, "y": 1, "button": "left"},
              {"t": 0.2, "kind": "mouse_up", "x": 1, "y": 1, "button": "left"}]
    player = MacroPlayer()
    t0 = time.time()
    _play(player, events, repeat=3, speed=4.0)
    assert time.time() - t0 < 0.5
    assert [c for c in null_input.recorded() if c == ("down", "left")].__len__() == 3


def test_empty_macro(null_input):
    player = MacroPlayer()
    assert player.play([]) is False
    assert player.last_error()["code"] == "macro.empty"


def test_macros_repo_roundtrip(tmp_path):
    import pytest

    from macros.repo import MacrosRepo

    repo = MacrosRepo(tmp_path)
    events = [{"t": 0.1, "kind": "mouse_move", "x": 1, "y": 2},
              {"t": 0.2, "kind": "key_down", "key": "A", "vk": 65}]
    assert repo.save("Coleta diária", events) == "Coleta diária"
    assert repo.list_macros() == ["Coleta diária"]
    assert repo.load("Coleta diária") == events
    with pytest.raises(ValueError):
        repo.save("vazia", [])
    with pytest.raises(ValueError):
        repo.save("ruim", [{"t": 0, "kind": "explodir"}])
    (tmp_path / "quebrada.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValueError):
        repo.load("quebrada")
    repo.delete("Coleta diária")
    assert "Coleta diária" not in repo.list_macros()


def test_controller_macro_save_load_play(app, null_input):
    import time as _t

    events = [{"t": 0.0, "kind": "mouse_down", "x": 5, "y": 5, "button": "left"},
              {"t": 0.01, "kind": "mouse_up", "x": 5, "y": 5, "button": "left"}]
    app._macro_recorder.set_events(events)
    state = app.macro_save("m1")
    assert state["saved_macro"] == "m1" and state["macros"] == ["m1"]
    assert state["macro"]["name"] == "m1" and state["macro"]["duration_ms"] == 10
    app.macro_clear()
    assert app.get_state()["macro"]["event_count"] == 0
    state = app.macro_load("m1")
    assert state["last_error"] is None and state["macro"]["event_count"] == 2
    state = app.macro_play(3, 5)
    assert state["macro"]["repeat"] == 3 and state["macro"]["speed"] == 5.0
    deadline = _t.time() + 3
    while app.get_state()["macro"]["playing"] and _t.time() < deadline:
        _t.sleep(0.01)
    assert null_input.recorded().count(("down", "left")) == 3
    assert app.macro_load("nao-existe")["last_error"]["code"] == "macro.notFound"
    assert app.macro_play("x", 1)["last_error"]["code"] == "macro.badOptions"
    assert app.macro_delete("m1")["macros"] == []
    assert app.get_settings()["macros"] == []
