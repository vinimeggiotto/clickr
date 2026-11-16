"""MacroPlayer — reproduz eventos gravados via backend de input."""

from __future__ import annotations

import sys
import threading
import time
from typing import Any, Callable, Optional

from core import sendinput
from core.errors import ClickrError, error_from_exception
from core.keys import name_to_vk
from core.sendinput import ButtonName

_BUTTONS = ("left", "right", "middle", "x1", "x2")


class MacroPlayer:
    """
    Reproduz lista de eventos com timestamps relativos.

    - repeat: número de execuções (>= 1); speed: fator de velocidade (> 0).
    - Ao terminar ou ser interrompido, solta toda tecla/botão ainda pressionado.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._playing = False
        self._events: list[dict[str, Any]] = []
        self._repeat = 1
        self._speed = 1.0
        self._iteration = 0
        self._last_error: Optional[dict[str, Any]] = None
        self._on_done: Optional[Callable[[], None]] = None
        self._on_tick: Optional[Callable[[], None]] = None
        # Recursos pressionados: ("vk", int) | ("char", str) | ("btn", str)
        self._pressed: list[tuple[str, Any]] = []

    def set_on_done(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_done = callback

    def set_on_tick(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_tick = callback

    def is_playing(self) -> bool:
        with self._lock:
            return self._playing

    def last_error(self) -> Optional[dict[str, Any]]:
        with self._lock:
            return self._last_error

    def clear_error(self) -> None:
        with self._lock:
            self._last_error = None

    def progress(self) -> dict[str, int]:
        with self._lock:
            return {"iteration": self._iteration, "repeat": self._repeat}

    def play(self, events: list[dict[str, Any]], repeat: int = 1, speed: float = 1.0) -> bool:
        with self._lock:
            if self._playing:
                return False
            if not events:
                self._last_error = ClickrError(
                    "macro.empty", "Macro vazia — grave eventos antes de reproduzir."
                ).to_dict()
                return False
            self._events = [dict(e) for e in events]
            self._repeat = max(1, int(repeat or 1))
            try:
                self._speed = float(speed or 1.0)
            except (TypeError, ValueError):
                self._speed = 1.0
            if self._speed <= 0:
                self._speed = 1.0
            self._iteration = 0
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
        if (
            thread is not None
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):
            thread.join(timeout=2.0)
        with self._lock:
            self._playing = False
            self._thread = None
        return True

    def _run(self) -> None:
        try:
            events = list(self._events)
            for iteration in range(self._repeat):
                if self._stop_event.is_set():
                    break
                with self._lock:
                    self._iteration = iteration + 1
                self._play_once(events)
                # Entre repetições nada deve ficar pressionado.
                self._release_all()
        except Exception as exc:
            with self._lock:
                self._last_error = error_from_exception(exc)
        finally:
            self._release_all()
            with self._lock:
                self._playing = False
                self._thread = None
            done = self._on_done
            if done is not None:
                try:
                    done()
                except Exception:
                    pass
            self._tick()

    def _play_once(self, events: list[dict[str, Any]]) -> None:
        t0 = time.perf_counter()
        for event in events:
            if self._stop_event.is_set():
                return
            target = float(event.get("t", 0) or 0) / self._speed
            while not self._stop_event.is_set():
                remaining = target - (time.perf_counter() - t0)
                if remaining <= 0:
                    break
                time.sleep(min(remaining, 0.01))
            if self._stop_event.is_set():
                return
            self._dispatch(event)
            self._tick()

    def _tick(self) -> None:
        cb = self._on_tick
        if cb is not None:
            try:
                cb()
            except Exception:
                pass

    # --- Pressionados ---------------------------------------------------

    def _mark(self, token: tuple[str, Any], down: bool) -> None:
        if down:
            if token not in self._pressed:
                self._pressed.append(token)
        elif token in self._pressed:
            self._pressed.remove(token)

    def _release_all(self) -> None:
        pressed, self._pressed = list(reversed(self._pressed)), []
        for kind, value in pressed:
            try:
                if kind == "vk":
                    sendinput.key_up(value)
                elif kind == "char":
                    sendinput.key_up_char(value)
                elif kind == "btn":
                    sendinput.button_up(value)
            except Exception:
                pass

    # --- Despacho -------------------------------------------------------

    def _dispatch(self, event: dict[str, Any]) -> None:
        kind = str(event.get("kind") or "")
        if kind == "mouse_move":
            sendinput.move_absolute(int(event["x"]), int(event["y"]))
        elif kind in ("mouse_down", "mouse_up"):
            down = kind == "mouse_down"
            button = self._button(event)
            sendinput.move_absolute(int(event["x"]), int(event["y"]))
            if down:
                sendinput.button_down(button)
            else:
                sendinput.button_up(button)
            self._mark(("btn", button), down)
        elif kind == "mouse_scroll":
            sendinput.move_absolute(int(event["x"]), int(event["y"]))
            sendinput.scroll(int(event.get("dy", 0) or 0), int(event.get("dx", 0) or 0))
        elif kind in ("key_down", "key_up"):
            self._key(event, kind == "key_down")
        else:
            raise ClickrError(
                "macro.unknownEvent", f"Evento de macro desconhecido: {kind}", kind=kind
            )

    def _key(self, event: dict[str, Any], down: bool) -> None:
        """
        Resolve a tecla pelo código gravado (Windows), pelo nome ou pelo
        caractere — nesta ordem. Eventos antigos (só "key") continuam válidos.
        """
        vk = event.get("vk")
        name = str(event.get("key") or "")
        char = event.get("char")
        code: Optional[int] = None
        if isinstance(vk, int) and sys.platform == "win32":
            code = vk
        else:
            try:
                code = name_to_vk(name)
            except ValueError:
                code = None
        if code is not None:
            (sendinput.key_down if down else sendinput.key_up)(code)
            self._mark(("vk", code), down)
            return
        if isinstance(char, str) and char:
            (sendinput.key_down_char if down else sendinput.key_up_char)(char)
            self._mark(("char", char), down)
            return
        raise ClickrError("macro.unsupportedKey", f"Tecla não suportada: {name}", key=name)

    @staticmethod
    def _button(event: dict[str, Any]) -> ButtonName:
        btn = str(event.get("button") or "left").lower()
        if btn not in _BUTTONS:
            btn = "left"
        return btn  # type: ignore[return-value]
