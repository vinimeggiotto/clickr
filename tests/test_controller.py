import json
import shutil
import time


def test_api_errors_do_not_raise(app):
    state = app.save_profile("CON")
    assert state["last_error"]["code"] == "profile.reservedName"
    # A próxima ação limpa o erro.
    assert app.set_config({"interval_ms": 30})["last_error"] is None


def test_get_state_does_not_touch_disk(app, tmp_path):
    shutil.rmtree(tmp_path / "Clickr" / "profiles", ignore_errors=True)
    state = app.get_state()
    assert "profiles" not in state
    assert not (tmp_path / "Clickr" / "profiles").exists()


def test_pick_overlay_is_transparent_and_close_resets(app):
    state = app.pick_location()
    assert state["picking"] is True
    overlay = app.test_webview.windows[-1]
    assert overlay.kwargs.get("transparent") is True
    overlay.destroy()  # fechado por fora (Alt+F4)
    assert app.get_state()["picking"] is False


def test_confirm_pick_sets_fixed_point(app, null_input):
    app.pick_location()
    null_input.set_cursor_pos_for_test(321, 123)
    state = app.confirm_pick()
    assert state["picking"] is False
    assert (state["config"]["fixed_x"], state["config"]["fixed_y"]) == (321, 123)
    assert state["config"]["position_mode"] == "fixed"


def test_does_not_click_on_own_window(app, null_input):
    win = app.test_window
    null_input.set_cursor_pos_for_test(win.x + 10, win.y + 10)
    app.set_config({"interval_ms": 2})
    app.start()
    time.sleep(0.08)
    assert app.get_state()["click_count"] == 0
    null_input.set_cursor_pos_for_test(win.x + win.width + 500, win.y)
    time.sleep(0.1)
    assert app.stop()["click_count"] > 0


def test_invalid_hotkey_keeps_previous(app):
    before = app.get_state()
    state = app.set_config({"hotkey": "NAO_EXISTE", "interval_ms": 44})
    assert state["last_error"]["code"] == "hotkey.unsupported"
    assert state["config"]["interval_ms"] == 44
    assert json.dumps(before["config"].get("hotkey")) == json.dumps(state["config"].get("hotkey"))


def test_state_is_pushed_to_ui(app):
    app.test_window.js.clear()
    app.set_config({"interval_ms": 3, "max_clicks": 3})
    null = __import__("core.sendinput_null", fromlist=["x"])
    null.set_cursor_pos_for_test(9000, 9000)
    app.start()
    time.sleep(0.4)
    pushed = [c for c in app.test_window.js if "__clickrApplyState" in c]
    assert pushed and '"click_count": 3' in pushed[-1]


def test_legacy_profile_loads_through_controller(app, tmp_path, fixtures_dir):
    profiles = tmp_path / "Clickr" / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixtures_dir / "profile_v1_envelope.json", profiles / "antigo.json")
    state = app.load_profile("antigo")
    assert state["last_error"] is None
    cfg = state["config"]
    assert cfg["interval_ms"] == 150 and cfg["button"] == "right"
    assert cfg["click_type"] == "double" and cfg["burst_count"] == 3
    assert len(cfg["sequence"]) == 2
    assert cfg["window_filter"]["process"] == "notepad.exe"
