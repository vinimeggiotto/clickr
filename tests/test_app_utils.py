import threading
import time

from app.notifier import UiNotifier
from app.single_instance import SingleInstance


def test_notifier_throttles():
    pushes = []
    n = UiNotifier(lambda: pushes.append(time.time()), min_interval_s=0.05)
    n.start()
    for _ in range(200):
        n.signal()
        time.sleep(0.001)
    time.sleep(0.12)
    n.stop()
    assert 2 <= len(pushes) <= 8


def test_notifier_delivers_last_signal():
    hit = threading.Event()
    n = UiNotifier(hit.set, min_interval_s=0.01)
    n.start()
    n.signal()
    assert hit.wait(1.0)
    n.stop()


def test_single_instance(tmp_path):
    first = SingleInstance(tmp_path)
    second = SingleInstance(tmp_path)
    assert first.acquire() is True
    assert second.acquire() is False
    shown = threading.Event()
    first.watch(shown.set, interval_s=0.02)
    second.request_show()
    assert shown.wait(1.0)
    first.release()
    third = SingleInstance(tmp_path)
    assert third.acquire() is True
    third.release()
