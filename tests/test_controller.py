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
    state = app.set_config({"hotkey": "NAO_EXISTE", "interval_ms": 44})
    assert state["last_error"]["code"] == "hotkey.unsupported"
    assert state["config"]["interval_ms"] == 44
    assert state["settings"]["hotkeys"]["toggle"] == "F6"


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
    # Perfil v1 continua trocando atalho e preferências, como na 1.0.1.
    assert state["settings"]["hotkeys"]["toggle"] == "F8"
    assert state["settings"]["always_on_top"] is False
    assert state["settings"]["compact_mode"] is True
    assert app.test_window.on_top is False
    # ...e o arquivo legado não foi reescrito.
    assert "version" not in json.loads((profiles / "antigo.json").read_text(encoding="utf-8"))


def test_legacy_raw_profile_merges_like_1_0(app, tmp_path, fixtures_dir):
    profiles = tmp_path / "Clickr" / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixtures_dir / "profile_v1_raw.json", profiles / "cru.json")
    app.set_config({"jitter_ms": 7})
    state = app.load_profile("cru")
    assert state["last_error"] is None
    assert state["config"]["interval_ms"] == 33 and state["config"]["click_type"] == "hold"
    assert state["config"]["jitter_ms"] == 7  # chave ausente no arquivo: mantém a atual
    assert state["settings"]["hotkeys"]["toggle"] == "F9"


def test_v2_profile_does_not_touch_app_preferences(app, tmp_path):
    app.set_config({"interval_ms": 21, "button": "middle"})
    assert app.save_profile("novo")["saved_profile"] == "novo"
    doc = json.loads((tmp_path / "Clickr" / "profiles" / "novo.json").read_text(encoding="utf-8"))
    assert doc["version"] == 2
    assert not {"hotkey", "always_on_top", "compact_mode"} & set(doc["config"])
    # Mesmo que alguém edite o arquivo à mão, v2 não altera preferências.
    doc["config"]["hotkey"] = "F10"
    doc["config"]["always_on_top"] = False
    (tmp_path / "Clickr" / "profiles" / "novo.json").write_text(json.dumps(doc), encoding="utf-8")
    app.set_config({"interval_ms": 99})
    state = app.load_profile("novo")
    assert state["config"]["interval_ms"] == 21 and state["config"]["button"] == "middle"
    assert state["settings"]["hotkeys"]["toggle"] == "F6"
    assert state["settings"]["always_on_top"] is True


def test_session_is_restored_on_next_start(app, tmp_path):
    app.set_config({"interval_ms": 123, "position_mode": "fixed", "fixed_x": 5, "fixed_y": 6})
    app.add_sequence_point(1, 2, 30)
    app.set_preferences({"compact_mode": True})
    app.save_script("click 1 2")
    app.shutdown()
    saved = json.loads((tmp_path / "Clickr" / "settings.json").read_text(encoding="utf-8"))
    assert saved["last_config"]["interval_ms"] == 123
    assert saved["last_script"] == "click 1 2"

    from app.controller import AppController

    again = AppController()
    try:
        state = again.get_state()
        assert state["config"]["interval_ms"] == 123
        assert state["config"]["sequence"] == [{"x": 1, "y": 2, "delay_ms": 30}]
        assert state["settings"]["compact_mode"] is True
        assert again.get_settings()["last_script"] == "click 1 2"
    finally:
        again.shutdown()


def test_tray_hint_and_manual_flags_persist(app):
    assert app.get_settings()["manual_seen"] is False
    app.set_manual_seen(True)
    assert app.get_settings()["manual_seen"] is True


def test_invalid_key_name_rejected(app):
    state = app.set_config({"action": "key", "key_name": "???"})
    assert state["last_error"]["code"] == "key.unsupported"
    assert state["config"]["action"] == "key" and state["config"]["key_name"] == "SPACE"


def test_legacy_profile_resets_new_fields(app, tmp_path, fixtures_dir):
    profiles = tmp_path / "Clickr" / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixtures_dir / "profile_v1_envelope.json", profiles / "antigo.json")
    app.set_config({"restore_cursor": True, "position_jitter_px": 9, "action": "key", "key_name": "E"})
    cfg = app.load_profile("antigo")["config"]
    assert cfg["restore_cursor"] is False and cfg["position_jitter_px"] == 0
    assert cfg["action"] == "mouse"
