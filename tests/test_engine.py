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
