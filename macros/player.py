"""MacroPlayer — reproduz eventos gravados via SendInput (caminho do motor)."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional

from core import sendinput
from core.sendinput import ButtonName


class MacroPlayer:
    """
    Reproduz lista de eventos com timestamps relativos usando SendInput.

    Parada: stop() ou hotkey via AppController.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._playing = False
        self._events: list[dict[str, Any]] = []
        self._last_error: Optional[str] = None
        self._on_done: Optional[Callable[[], None]] = None
        self._on_tick: Optional[Callable[[], None]] = None

    def set_on_done(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_done = callback

    def set_on_tick(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_tick = callback

    def is_playing(self) -> bool:
        with self._lock:
            return self._playing

    def last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    def play(self, events: list[dict[str, Any]]) -> bool:
        with self._lock:
            if self._playing:
                return False
            if not events:
                self._last_error = "Macro vazia — grave eventos antes de reproduzir."
                return False
            self._events = [dict(e) for e in events]
            self._last_error = None
            self._stop_event.clear()
            self._playing = True
            self._thread = threading.Thread(target=self._run, name="MacroPlayer", daemon=True)
            self._thread.start()
            return True

    def stop(self) -> bool:
        with self._lock:
            if not self._playing and self._thread is None:
                return False
            self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            self._playing = False
            self._thread = None
        return True

    def _run(self) -> None:
        try:
            events = list(self._events)
            t0 = time.perf_counter()
            for event in events:
                if self._stop_event.is_set():
                    break
                target = float(event.get("t", 0) or 0)
                while not self._stop_event.is_set():
                    elapsed = time.perf_counter() - t0
                    remaining = target - elapsed
                    if remaining <= 0:
                        break
                    time.sleep(min(remaining, 0.01))
                if self._stop_event.is_set():
                    break
                self._dispatch(event)
                self._tick()
        except Exception as exc:
            with self._lock:
                self._last_error = str(exc)
        finally:
            with self._lock:
                self._playing = False
                self._thread = None
            done = self._on_done
            if done is not None:
                done()
            self._tick()

    def _tick(self) -> None:
        cb = self._on_tick
        if cb is not None:
            cb()

    def _dispatch(self, event: dict[str, Any]) -> None:
        kind = str(event.get("kind") or "")
        if kind == "mouse_move":
            sendinput.move_absolute(int(event["x"]), int(event["y"]))
        elif kind == "mouse_down":
            x, y = int(event["x"]), int(event["y"])
            sendinput.move_absolute(x, y)
            sendinput.button_down(self._button(event))
        elif kind == "mouse_up":
            x, y = int(event["x"]), int(event["y"])
            sendinput.move_absolute(x, y)
            sendinput.button_up(self._button(event))
        elif kind == "key_down":
            sendinput.key_down_name(str(event["key"]))
        elif kind == "key_up":
            sendinput.key_up_name(str(event["key"]))
        else:
            raise ValueError(f"Evento de macro desconhecido: {kind}")

    @staticmethod
    def _button(event: dict[str, Any]) -> ButtonName:
        btn = str(event.get("button") or "left").lower()
        if btn not in ("left", "right", "middle", "x1", "x2"):
            btn = "left"
        return btn  # type: ignore[return-value]
