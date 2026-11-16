import threading
import time
from datetime import datetime, timedelta

import pytest

from scheduler.service import Scheduler, normalize_schedule


class Clock:
    def __init__(self, start):
        self.value = start

    def __call__(self):
        return self.value

    def advance(self, **kw):
        self.value += timedelta(**kw)


def _wait(event, timeout=2.0):
    assert event.wait(timeout), "não disparou"


def test_once_fires_and_clears():
    clock = Clock(datetime(2026, 1, 1, 10, 0, 0))
    fired = []
    hit = threading.Event()
    s = Scheduler(now=clock)
    s.schedule(datetime(2026, 1, 1, 10, 0, 5), lambda item: (fired.append(item), hit.set()))
    assert s.status()["active"] and s.status()["at"] == "2026-01-01T10:00:05"
    time.sleep(0.1)
    assert not fired
    clock.advance(seconds=6)
    _wait(hit)
    assert fired[0]["target"] == "engine"
    assert s.status()["active"] is False
    s.shutdown()


def test_past_time_rejected_for_once():
    clock = Clock(datetime(2026, 1, 1, 10, 0, 0))
    s = Scheduler(now=clock)
    with pytest.raises(ValueError):
        s.schedule(datetime(2026, 1, 1, 9, 0, 0), lambda item: None)
    s.shutdown()


def test_daily_rolls_to_next_day_and_survives_clock_jump():
    clock = Clock(datetime(2026, 1, 1, 10, 0, 0))
    hits = []
    hit = threading.Event()
    s = Scheduler(now=clock)
    s.schedule(datetime(2026, 1, 1, 8, 30, 0), lambda item: (hits.append(item), hit.set()), repeat="daily")
    assert s.status()["at"] == "2026-01-02T08:30:00"
    # Computador "suspenso" por dois dias: dispara uma vez e agenda o próximo dia.
    clock.advance(days=2)
    _wait(hit)
    time.sleep(0.1)
    assert len(hits) == 1
    assert s.status()["active"] and s.status()["at"] == "2026-01-04T08:30:00"
    s.shutdown()


def test_interval_repeats():
    clock = Clock(datetime(2026, 1, 1, 10, 0, 0))
    hits = []
    s = Scheduler(now=clock)
    s.schedule(datetime(2026, 1, 1, 10, 0, 10), lambda item: hits.append(1), repeat="interval", interval_s=60)
    for _ in range(3):
        clock.advance(seconds=61)
        s._wake.set()  # relógio falso: acorda o laço em vez de esperar 1 s real
        time.sleep(0.15)
    assert len(hits) == 3 and s.status()["active"]
    s.cancel()
    assert not s.status()["active"]
    s.shutdown()


def test_restore_rules():
    clock = Clock(datetime(2026, 1, 5, 12, 0, 0))
    s = Scheduler(now=clock)
    assert s.restore({"at": "2026-01-01T08:00:00", "repeat": "once"}) is False
    assert s.restore({"at": "2026-01-01T08:00:00", "repeat": "daily", "target": "script"}) is True
    assert s.status()["at"] == "2026-01-06T08:00:00" and s.status()["target"] == "script"
    assert s.restore({"at": "2026-01-09T08:00:00", "repeat": "once"}) is True
    assert s.restore({"lixo": 1}) is False
    s.shutdown()


@pytest.mark.parametrize(
    "data",
    [
        {"at": ""},
        {"at": "ontem"},
        {"at": "2026-01-01T10:00", "repeat": "semanal"},
        {"at": "2026-01-01T10:00", "target": "foguete"},
        {"at": "2026-01-01T10:00", "repeat": "interval", "interval_s": 1},
        {"at": "2026-01-01T10:00", "target": "profile"},
    ],
)
def test_validation(data):
    with pytest.raises(ValueError):
        normalize_schedule(data)


def test_callback_error_is_reported():
    clock = Clock(datetime(2026, 1, 1, 10, 0, 0))
    s = Scheduler(now=clock)

    def boom(item):
        raise RuntimeError("falhou")

    s.schedule(datetime(2026, 1, 1, 10, 0, 1), boom)
    clock.advance(seconds=2)
    time.sleep(0.2)
    assert s.last_error() is not None
    s.shutdown()
