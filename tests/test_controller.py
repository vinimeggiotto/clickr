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


def test_sequence_edit_and_move(app):
    app.add_sequence_point(1, 1, 10)
    app.add_sequence_point(2, 2, 20)
    app.add_sequence_point(3, 3, 30)
    state = app.update_sequence_point(1, {"delay_ms": 250, "x": 22})
    assert state["config"]["sequence"][1] == {"x": 22, "y": 2, "delay_ms": 250}
    state = app.move_sequence_point(2, 0)
    assert [s["x"] for s in state["config"]["sequence"]] == [3, 1, 22]
    assert app.move_sequence_point(9, 0)["last_error"]["code"] == "sequence.badIndex"
    assert app.update_sequence_point(0, {"delay_ms": "abc"})["last_error"]["code"] == "config.invalid"


def test_pick_into_sequence(app, null_input):
    app.pick_location("sequence", 120)
    null_input.set_cursor_pos_for_test(40, 50)
    state = app.confirm_pick()
    assert state["config"]["sequence"] == [{"x": 40, "y": 50, "delay_ms": 120}]
    assert state["config"]["position_mode"] == "cursor"  # ponto fixo não foi alterado


def test_capture_foreground_window(app, monkeypatch):
    monkeypatch.setattr(
        app._engine.window_filter, "foreground_info", lambda: ("notepad.exe", "Sem título")
    )
    state = app.capture_foreground_window(0.5)
    assert state["window_capture"]["active"] is True
    time.sleep(0.8)
    state = app.get_state()
    assert state["window_capture"]["active"] is False
    assert state["config"]["window_filter"] == {
        "enabled": True, "process": "notepad.exe", "title_contains": "Sem título",
    }


def test_capture_foreground_window_failure_is_reported(app, monkeypatch):
    def boom():
        raise OSError("xprop ausente")

    monkeypatch.setattr(app._engine.window_filter, "foreground_info", boom)
    app.capture_foreground_window(0.5)
    time.sleep(0.8)
    assert app.get_state()["last_error"]["code"] == "filter.unavailable"


def test_profile_delete_and_rename_via_controller(app):
    app.save_profile("um")
    app.save_profile("dois")
    state = app.rename_profile("um", "três")
    assert state["renamed_profile"] == "três" and state["profiles"] == ["dois", "três"]
    assert app.rename_profile("dois", "três")["last_error"]["code"] == "profile.exists"
    state = app.delete_profile("dois")
    assert state["deleted_profile"] == "dois" and state["profiles"] == ["três"]
    assert app.delete_profile("dois")["last_error"]["code"] == "profile.notFound"


def test_import_asks_before_overwriting(app, tmp_path, fixtures_dir):
    app.set_config({"interval_ms": 77})
    app.save_profile("farm-legado")
    app.test_window.dialog_result = [str(fixtures_dir / "profile_v1_envelope.json")]
    state = app.import_profile("")
    assert state["import_conflict"] == "farm-legado"
    assert state["config"]["interval_ms"] == 77  # nada aplicado ainda
    saved = json.loads((tmp_path / "Clickr" / "profiles" / "farm-legado.json").read_text(encoding="utf-8"))
    assert saved["config"]["interval_ms"] == 77
    state = app.import_profile_confirm()
    assert state["imported_profile"] == "farm-legado" and state["config"]["interval_ms"] == 150
    # Sem conflito importa direto.
    app.test_window.dialog_result = [str(fixtures_dir / "profile_v1_raw.json")]
    assert app.import_profile("")["imported_profile"] == "profile_v1_raw"


def test_schedule_targets_and_persistence(app, tmp_path, null_input):
    null_input.set_cursor_pos_for_test(9000, 9000)
    from datetime import datetime, timedelta

    soon = (datetime.now() + timedelta(seconds=1.2)).isoformat(timespec="seconds")
    app.save_script("click 4 4\nwait 300")
    state = app.schedule_set(soon, {"target": "script"})
    assert state["last_error"] is None and state["schedule"]["target"] == "script"
    saved = json.loads((tmp_path / "Clickr" / "settings.json").read_text(encoding="utf-8"))
    assert saved["schedule"]["target"] == "script"
    deadline = time.time() + 4
    while time.time() < deadline and ("click", "left") not in null_input.recorded():
        time.sleep(0.05)
    assert ("click", "left") in null_input.recorded()
    assert app.get_state()["schedule"]["active"] is False
    saved = json.loads((tmp_path / "Clickr" / "settings.json").read_text(encoding="utf-8"))
    assert saved["schedule"] is None


def test_recurring_schedule_survives_restart(app, tmp_path):
    state = app.schedule_set("2020-01-01T07:30:00", {"repeat": "daily", "target": "engine"})
    assert state["last_error"] is None and state["schedule"]["repeat"] == "daily"
    app.shutdown()
    from app.controller import AppController

    again = AppController()
    again.bootstrap_services()
    try:
        sched = again.get_state()["schedule"]
        assert sched["active"] and sched["repeat"] == "daily" and sched["at"].endswith("T07:30:00")
    finally:
        again.shutdown()


def test_schedule_validation_errors(app):
    assert app.schedule_set("", {})["last_error"]["code"] == "schedule.empty"
    assert app.schedule_set("2020-01-01T00:00", {})["last_error"]["code"] == "schedule.past"
    err = app.schedule_set("2999-01-01T00:00", {"target": "profile", "profile": "nao"})["last_error"]
    assert err["code"] == "profile.notFound"
    err = app.schedule_set("2999-01-01T00:00", {"repeat": "interval", "interval_s": 1})["last_error"]
    assert err["code"] == "schedule.badInterval"


def test_autostart_preference(app, monkeypatch):
    calls = []
    monkeypatch.setattr("app.autostart.set_enabled", lambda enabled, **kw: calls.append(enabled))
    assert app.set_preferences({"launch_at_login": True})["settings"]["launch_at_login"] is True
    assert calls == [True]

    def boom(enabled, **kw):
        raise OSError("acesso negado")

    monkeypatch.setattr("app.autostart.set_enabled", boom)
    state = app.set_preferences({"launch_at_login": False})
    assert state["last_error"]["code"] == "autostart.failed"
    assert state["settings"]["launch_at_login"] is True  # preferência não muda se o SO recusar


def test_update_check_reports_new_version(app, monkeypatch):
    monkeypatch.setattr(
        "app.updates.check_latest",
        lambda current, **kw: {"version": "9.9.9", "url": "https://github.com/vinimeggiotto/clickr/releases/tag/v9.9.9"},
    )
    assert app.get_state()["update"] is None
    app.set_preferences({"check_updates": True})
    deadline = time.time() + 2
    while time.time() < deadline and app.get_state()["update"] is None:
        time.sleep(0.02)
    assert app.get_state()["update"]["version"] == "9.9.9"


def test_update_check_failure_is_silent(app, monkeypatch):
    def boom(current, **kw):
        raise OSError("sem rede")

    monkeypatch.setattr("app.updates.check_latest", boom)
    state = app.check_updates_now()
    time.sleep(0.2)
    assert app.get_state()["update"] is None and app.get_state()["last_error"] is None
