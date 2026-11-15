import time

import pytest

from hotkeys.combo import parse_combo
from macros.recorder import sanitize_events


def test_parse_combo_canonical():
    assert str(parse_combo("f6")) == "F6"
    assert str(parse_combo("alt + ctrl + f6")) == "CTRL+ALT+F6"
    assert str(parse_combo("Shift+a")) == "SHIFT+A"
    assert str(parse_combo("control+win+space")) == "CTRL+WIN+SPACE"


@pytest.mark.parametrize("text", ["", "CTRL", "CTRL+SHIFT", "FOO+A", "CTRL+???", "A+B"])
def test_parse_combo_rejects(text):
    with pytest.raises(ValueError):
        parse_combo(text)


@pytest.fixture()
def service(app):
    return app._hotkeys


def _kb(fakes):
    return [l for l in fakes.listeners() if type(l).__name__ == "KeyboardListener" and l.running]


def _key(name):
    import sys

    return getattr(sys.modules["pynput.keyboard"].Key, name)


def _char(ch):
    import sys

    return sys.modules["pynput.keyboard"].KeyCode.from_char(ch)


def _press(listener, *keys):
    for key in keys:
        listener.emit("on_press", key)


def _release(listener, *keys):
    for key in keys:
        listener.emit("on_release", key)


def _wait(predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_toggle_hotkey_starts_and_stops_engine(app, null_input):
    import fakes

    null_input.set_cursor_pos_for_test(9000, 9000)
    listener = _kb(fakes)[0]
    _press(listener, _key("f6"))
    assert _wait(lambda: app.get_state()["engine_running"])
    # Auto-repetição da tecla não alterna de novo.
    _press(listener, _key("f6"))
    _press(listener, _key("f6"))
    time.sleep(0.1)
    assert app.get_state()["engine_running"]
    _release(listener, _key("f6"))
    _press(listener, _key("f6"))
    assert _wait(lambda: not app.get_state()["engine_running"])


def test_modifier_combo_only_fires_with_modifiers(app, null_input):
    import fakes

    null_input.set_cursor_pos_for_test(9000, 9000)
    state = app.set_hotkey("toggle", "ctrl+shift+a")
    assert state["settings"]["hotkeys"]["toggle"] == "CTRL+SHIFT+A"
    listener = _kb(fakes)[0]
    _press(listener, _char("a"))
    _release(listener, _char("a"))
    time.sleep(0.1)
    assert not app.get_state()["engine_running"]
    _press(listener, _key("ctrl_l"), _key("shift"), _char("A"))
    assert _wait(lambda: app.get_state()["engine_running"])
    app.stop()


def test_conflict_and_validation(app):
    assert app.set_hotkey("stop_all", "F6")["last_error"]["code"] == "hotkey.conflict"
    assert app.set_hotkey("stop_all", "CTRL")["last_error"]["code"] == "hotkey.unsupported"
    assert app.clear_hotkey("toggle")["last_error"]["code"] == "hotkey.toggleRequired"
    state = app.set_hotkey("stop_all", "F7")
    assert state["last_error"] is None and state["settings"]["hotkeys"]["stop_all"] == "F7"
    assert app.clear_hotkey("stop_all")["settings"]["hotkeys"]["stop_all"] == ""


def test_stop_all_hotkey(app, null_input):
    import fakes

    null_input.set_cursor_pos_for_test(9000, 9000)
    app.set_hotkey("stop_all", "F7")
    app.script_run("wait 5000")
    assert app.get_state()["script"]["running"]
    _press(_kb(fakes)[0], _key("f7"))
    assert _wait(lambda: not app.get_state()["running"])


def test_pick_point_hotkey_uses_cursor(app, null_input):
    import fakes

    app.set_hotkey("pick_point", "F8")
    null_input.set_cursor_pos_for_test(777, 333)
    _press(_kb(fakes)[0], _key("f8"))
    assert _wait(lambda: app.get_state()["config"]["fixed_x"] == 777)
    cfg = app.get_state()["config"]
    assert cfg["fixed_y"] == 333 and cfg["position_mode"] == "fixed"


def test_capture_records_combo_and_suspends_hotkeys(app, null_input):
    import fakes

    null_input.set_cursor_pos_for_test(9000, 9000)
    state = app.record_hotkey("stop_all")
    assert state["recording_hotkey"] and state["recording_hotkey_action"] == "stop_all"
    main, capture = _kb(fakes)[0], _kb(fakes)[-1]
    assert main is not capture
    # F6 durante a captura não liga o motor.
    _press(main, _key("f6"))
    _release(main, _key("f6"))
    time.sleep(0.1)
    assert not app.get_state()["engine_running"]
    _press(capture, _key("ctrl_l"), _key("alt_l"), _key("f9"))
    assert _wait(lambda: app.get_state()["settings"]["hotkeys"]["stop_all"] == "CTRL+ALT+F9")
    assert app.get_state()["recording_hotkey"] is False


def test_capture_escape_cancels(app):
    import fakes

    app.record_hotkey("toggle")
    _press(_kb(fakes)[-1], _key("esc"))
    assert _wait(lambda: app.get_state()["recording_hotkey"] is False)
    assert app.get_state()["settings"]["hotkeys"]["toggle"] == "F6"


def test_hold_to_click(app, null_input):
    import fakes

    null_input.set_cursor_pos_for_test(9000, 9000)
    app.set_preferences({"activation": "hold"})
    app.set_config({"interval_ms": 5})
    listener = _kb(fakes)[0]
    _press(listener, _key("f6"))
    assert _wait(lambda: app.get_state()["engine_running"])
    time.sleep(0.15)
    assert app.get_state()["engine_running"], "parou com a tecla ainda pressionada"
    _release(listener, _key("f6"))
    assert _wait(lambda: not app.get_state()["engine_running"])
    assert app.get_state()["click_count"] > 3


def test_bindings_survive_restart(app, tmp_path):
    app.set_hotkey("toggle", "ALT+F2")
    app.set_hotkey("macro_record", "F10")
    app.shutdown()
    from app.controller import AppController

    again = AppController()
    try:
        hotkeys = again.get_state()["settings"]["hotkeys"]
        assert hotkeys["toggle"] == "ALT+F2" and hotkeys["macro_record"] == "F10"
    finally:
        again.shutdown()


def test_sanitize_strips_recording_hotkey():
    events = [
        {"t": 0.0, "kind": "key_up", "key": "F10"},          # soltura do atalho que iniciou
        {"t": 0.1, "kind": "key_down", "key": "A"},
        {"t": 0.2, "kind": "key_up", "key": "A"},
        {"t": 0.3, "kind": "key_down", "key": "CTRL L"},     # atalho de parar: CTRL+F10
        {"t": 0.4, "kind": "mouse_move", "x": 1, "y": 1},
        {"t": 0.5, "kind": "key_down", "key": "F10"},
    ]
    out = sanitize_events(events, parse_combo("CTRL+F10").tokens())
    assert [(e["kind"], e.get("key")) for e in out] == [
        ("key_down", "A"), ("key_up", "A"), ("mouse_move", None),
    ]


def test_sanitize_keeps_user_keys():
    events = [
        {"t": 0.0, "kind": "key_down", "key": "SHIFT"},
        {"t": 0.1, "kind": "mouse_down", "x": 1, "y": 1, "button": "left"},
        {"t": 0.2, "kind": "mouse_up", "x": 1, "y": 1, "button": "left"},
        {"t": 0.3, "kind": "mouse_up", "x": 1, "y": 1, "button": "right"},  # órfão
    ]
    out = sanitize_events(events, {0x79})
    assert len(out) == 3 and out[0]["key"] == "SHIFT"
