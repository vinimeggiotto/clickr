import time

from core.engine import ClickEngine


def _wait_stopped(engine, timeout=3.0):
    deadline = time.time() + timeout
    while engine.is_running() and time.time() < deadline:
        time.sleep(0.005)
    assert not engine.is_running()


def test_max_clicks_stops(null_input):
    engine = ClickEngine()
    engine.update_config({"interval_ms": 1, "max_clicks": 5})
    engine.start()
    _wait_stopped(engine)
    assert engine.get_state().click_count == 5
    assert [c[0] for c in null_input.recorded()].count("click") == 5


def test_fixed_point_moves(null_input):
    engine = ClickEngine()
    engine.update_config(
        {"interval_ms": 1, "max_clicks": 2, "position_mode": "fixed", "fixed_x": 7, "fixed_y": 9}
    )
    engine.start()
    _wait_stopped(engine)
    assert ("move", 7, 9) in null_input.recorded()


def test_sequence_and_double(null_input):
    engine = ClickEngine()
    engine.update_config(
        {
            "interval_ms": 1,
            "max_clicks": 4,
            "click_type": "double",
            "sequence": [{"x": 1, "y": 1, "delay_ms": 0}, {"x": 2, "y": 2, "delay_ms": 0}],
        }
    )
    engine.start()
    _wait_stopped(engine)
    moves = [c for c in null_input.recorded() if c[0] == "move"]
    assert ("move", 1, 1) in moves and ("move", 2, 2) in moves
    assert engine.get_state().click_count == 4


def test_hold_presses_and_releases(null_input):
    engine = ClickEngine()
    engine.update_config({"click_type": "hold", "button": "right"})
    engine.start()
    time.sleep(0.1)
    engine.stop()
    rec = null_input.recorded()
    assert ("down", "right") in rec and ("up", "right") in rec


def test_stop_and_toggle(null_input):
    engine = ClickEngine()
    engine.update_config({"interval_ms": 5})
    assert engine.toggle() is True
    time.sleep(0.05)
    assert engine.toggle() is False
    assert not engine.is_running()


def test_notifies_when_limit_reached(null_input):
    engine = ClickEngine()
    seen = []
    engine.set_on_tick(lambda: seen.append(engine.is_running()))
    engine.update_config({"interval_ms": 1, "max_clicks": 3})
    engine.start()
    _wait_stopped(engine)
    time.sleep(0.05)
    assert seen and seen[-1] is False


def test_hold_releases_pressed_button_even_if_config_changes(null_input):
    engine = ClickEngine()
    engine.update_config({"click_type": "hold", "button": "right"})
    engine.start()
    time.sleep(0.08)
    engine.update_config({"button": "left"})
    engine.stop()
    rec = null_input.recorded()
    assert ("up", "right") in rec
    assert ("up", "left") not in rec


def test_click_guard_blocks(null_input):
    engine = ClickEngine()
    engine.set_click_guard(lambda x, y: True)
    engine.update_config({"interval_ms": 2})
    engine.start()
    time.sleep(0.06)
    engine.stop()
    assert [c for c in null_input.recorded() if c[0] == "click"] == []
    assert engine.get_state().click_count == 0


def test_rate_is_close_to_interval(null_input):
    engine = ClickEngine()
    engine.update_config({"interval_ms": 10})
    engine.start()
    time.sleep(0.5)
    engine.stop()
    n = engine.get_state().click_count
    assert 40 <= n <= 56, n


def test_restore_cursor(null_input):
    null_input.set_cursor_pos_for_test(500, 500)
    engine = ClickEngine()
    engine.update_config(
        {"interval_ms": 1, "max_clicks": 2, "position_mode": "fixed", "fixed_x": 10, "fixed_y": 20,
         "restore_cursor": True}
    )
    engine.start()
    _wait_stopped(engine)
    rec = null_input.recorded()
    assert rec[:3] == [("move", 10, 20), ("click", "left"), ("move", 500, 500)]
    assert null_input.get_cursor_pos() == (500, 500)


def test_position_jitter_stays_in_range(null_input):
    engine = ClickEngine()
    engine.update_config(
        {"interval_ms": 1, "max_clicks": 40, "position_mode": "fixed", "fixed_x": 100,
         "fixed_y": 100, "position_jitter_px": 5}
    )
    engine.start()
    _wait_stopped(engine)
    moves = [c for c in null_input.recorded() if c[0] == "move"]
    assert len(moves) == 40
    assert all(95 <= x <= 105 and 95 <= y <= 105 for _, x, y in moves)
    assert len({(x, y) for _, x, y in moves}) > 3


def test_key_action(null_input):
    engine = ClickEngine()
    engine.update_config({"interval_ms": 1, "max_clicks": 3, "action": "key", "key_name": "ctrl+e"})
    engine.start()
    _wait_stopped(engine)
    rec = null_input.recorded()
    assert rec[:4] == [("key_down", 0x11), ("key_down", ord("E")), ("key_up", ord("E")), ("key_up", 0x11)]
    assert [c for c in rec if c[0] == "click"] == []
    assert engine.get_state().click_count == 3


def test_key_hold_releases(null_input):
    engine = ClickEngine()
    engine.update_config({"action": "key", "key_name": "W", "click_type": "hold"})
    engine.start()
    time.sleep(0.08)
    engine.stop()
    rec = null_input.recorded()
    assert rec.count(("key_down", ord("W"))) == 1 and rec.count(("key_up", ord("W"))) == 1


def test_key_guard_blocks(null_input):
    engine = ClickEngine()
    engine.set_key_guard(lambda: True)
    engine.update_config({"interval_ms": 2, "action": "key", "key_name": "A"})
    engine.start()
    time.sleep(0.05)
    engine.stop()
    assert null_input.recorded() == []


def test_countdown_then_running_state(null_input):
    engine = ClickEngine()
    engine.update_config({"interval_ms": 10, "start_delay_ms": 200})
    engine.start()
    time.sleep(0.05)
    st = engine.get_state()
    assert st.phase == "countdown" and st.starts_at is not None and st.click_count == 0
    assert 0 < st.starts_at - time.time() < 0.25
    time.sleep(0.4)
    st = engine.get_state()
    assert st.phase == "running" and st.starts_at is None
    assert 100 <= st.elapsed_ms <= 400
    engine.stop()
    final = engine.get_state()
    assert final.phase == "idle" and final.elapsed_ms >= 100
    time.sleep(0.05)
    assert engine.get_state().elapsed_ms == final.elapsed_ms  # congelado


def test_actual_cps_and_sequence_index(null_input):
    engine = ClickEngine()
    engine.update_config(
        {"interval_ms": 20, "sequence": [{"x": 1, "y": 1, "delay_ms": 20}, {"x": 2, "y": 2, "delay_ms": 20}]}
    )
    assert engine.get_state().sequence_index == 0
    engine.start()
    time.sleep(1.3)
    st = engine.get_state()
    assert 35 <= st.actual_cps <= 55, st.actual_cps
    assert st.sequence_index in (0, 1)
    engine.stop()
    assert engine.get_state().actual_cps == 0.0


def test_blocked_reason_is_reported(null_input):
    engine = ClickEngine()
    engine.set_click_guard(lambda x, y: True)
    engine.update_config({"interval_ms": 5})
    engine.start()
    time.sleep(0.06)
    assert engine.get_state().blocked == "own_window"
    engine.set_click_guard(None)
    time.sleep(0.06)
    assert engine.get_state().blocked is None
    engine.stop()
    assert engine.get_state().blocked is None


def test_stop_does_not_clobber_a_run_started_meanwhile(null_input):
    """stop() concorrente com start() não pode deixar um loop órfão."""
    import threading

    engine = ClickEngine()
    engine.update_config({"interval_ms": 2})
    for _ in range(40):
        engine.start()
        stopper = threading.Thread(target=engine.stop)
        stopper.start()
        engine.start()
        stopper.join()
        # Qualquer que seja a ordem, um stop() final precisa parar tudo.
        engine.stop()
        assert not engine.is_running()
        before = len(null_input.recorded())
        time.sleep(0.02)
        assert len(null_input.recorded()) == before, "loop órfão continuou clicando"
