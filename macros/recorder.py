"""MacroRecorder — captura eventos de mouse/teclado com timestamps (pynput)."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional

from core.keys import modifier_family, name_to_vk
from core.sendinput import button_from_pynput
from hotkeys.keynames import describe_key

# Throttle de movimentos para não explodir a lista
_MOVE_MIN_INTERVAL_S = 0.016


def _key_token(event: dict[str, Any]) -> Any:
    """Identificador da tecla de um evento: família do modificador, vk ou nome."""
    vk = event.get("vk")
    if not isinstance(vk, int):
        try:
            vk = name_to_vk(str(event.get("key") or ""))
        except ValueError:
            return str(event.get("key") or "")
    return modifier_family(vk) or vk


def sanitize_events(
    events: list[dict[str, Any]], strip_tokens: Optional[set] = None
) -> list[dict[str, Any]]:
    """
    Limpa as pontas de uma gravação:
    - remove key_up sem key_down anterior (tecla já estava pressionada ao iniciar);
    - remove, do fim, os eventos das teclas do atalho de gravação;
    - remove key_down/mouse_down que ficaram sem o respectivo "up".
    """
    strip = set(strip_tokens or ())
    out = [dict(e) for e in events]

    # Do fim para o começo: eventos do atalho (movimentos de mouse são mantidos).
    if strip:
        index = len(out) - 1
        while index >= 0:
            event = out[index]
            kind = event.get("kind")
            if kind == "mouse_move":
                index -= 1
                continue
            if kind in ("key_down", "key_up") and _key_token(event) in strip:
                del out[index]
                index -= 1
                continue
            break

    held: dict[Any, int] = {}
    cleaned: list[dict[str, Any]] = []
    for event in out:
        kind = event.get("kind")
        if kind in ("key_down", "key_up"):
            token: Any = ("key", _key_token(event))
        elif kind in ("mouse_down", "mouse_up"):
            token = ("btn", event.get("button"))
        else:
            cleaned.append(event)
            continue
        if kind.endswith("_down"):
            held[token] = len(cleaned)
            cleaned.append(event)
        elif token in held:
            del held[token]
            cleaned.append(event)
        # "up" órfão: descartado
    # "down" sem "up": só os do atalho são removidos (os demais são soltos pelo player).
    orphan_indexes = {
        index for token, index in held.items()
        if token[0] == "key" and token[1] in strip
    }
    return [event for index, event in enumerate(cleaned) if index not in orphan_indexes]


class MacroRecorder:
    """
    Grava eventos mouse/teclado relativos ao instante de início.

    Formato de evento:
      {"t": float, "kind": str, ...campos por kind}
    kinds: mouse_move, mouse_down, mouse_up, mouse_scroll, key_down, key_up
    Eventos de tecla: {"key": nome, "vk"?: código Win32, "char"?: caractere}.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: list[dict[str, Any]] = []
        self._recording = False
        self._t0: float = 0.0
        self._last_move_t: float = -1.0
        self._mouse_listener: Any = None
        self._key_listener: Any = None
        self._on_change: Optional[Callable[[], None]] = None
        self._ignore_point: Optional[Callable[[int, int], bool]] = None

    def set_ignore_point(self, predicate: Optional[Callable[[int, int], bool]]) -> None:
        """predicate(x, y) → True faz cliques naquele ponto não serem gravados
        (ex.: cliques nos botões do próprio Clickr)."""
        self._ignore_point = predicate

    def set_on_change(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_change = callback

    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

    def event_count(self) -> int:
        with self._lock:
            return len(self._events)

    def get_events(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(e) for e in self._events]

    def set_events(self, events: list[dict[str, Any]]) -> None:
        with self._lock:
            self._events = [dict(e) for e in events]

    def duration_ms(self) -> int:
        with self._lock:
            if not self._events:
                return 0
            return int(float(self._events[-1].get("t", 0) or 0) * 1000)

    def clear(self) -> None:
        with self._lock:
            self._events = []
        self._notify()

    def start(self) -> bool:
        # Import tardio: pynput exige display/permissões e não deve ser
        # carregado só por importar o pacote.
        from pynput import keyboard, mouse

        with self._lock:
            if self._recording:
                return False
            self._events = []
            self._recording = True
            self._t0 = time.perf_counter()
            self._last_move_t = -1.0

            self._mouse_listener = mouse.Listener(
                on_move=self._on_move,
                on_click=self._on_click,
                on_scroll=self._on_scroll,
            )
            self._key_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self._mouse_listener.daemon = True
            self._key_listener.daemon = True
            self._mouse_listener.start()
            self._key_listener.start()
        self._notify()
        return True

    def stop(self, strip_tokens: Optional[set] = None) -> list[dict[str, Any]]:
        """
        Encerra a gravação e devolve os eventos.

        strip_tokens: teclas do atalho que iniciou/parou a gravação (famílias de
        modificador ou códigos VK); seus eventos nas pontas são removidos para
        que o próprio atalho não entre na macro.
        """
        with self._lock:
            was_recording = self._recording
            self._recording = False
            mouse_l = self._mouse_listener
            key_l = self._key_listener
            self._mouse_listener = None
            self._key_listener = None
            if was_recording:
                self._events = sanitize_events(self._events, strip_tokens)
            events = [dict(e) for e in self._events]
        if mouse_l is not None:
            mouse_l.stop()
        if key_l is not None:
            key_l.stop()
        self._notify()
        return events

    def _elapsed(self) -> float:
        return time.perf_counter() - self._t0

    def _append(self, event: dict[str, Any]) -> None:
        with self._lock:
            if not self._recording:
                return
            self._events.append(event)
        self._notify()

    def _on_move(self, x: int, y: int) -> None:
        with self._lock:
            if not self._recording:
                return
            now = self._elapsed()
            if self._last_move_t >= 0 and (now - self._last_move_t) < _MOVE_MIN_INTERVAL_S:
                return
            self._last_move_t = now
            self._events.append({"t": now, "kind": "mouse_move", "x": int(x), "y": int(y)})
        self._notify()

    def _on_click(self, x: int, y: int, button: object, pressed: bool) -> None:
        btn = button_from_pynput(button)
        if btn is None:
            return
        ignore = self._ignore_point
        if ignore is not None:
            try:
                if ignore(int(x), int(y)):
                    return
            except Exception:
                pass
        kind = "mouse_down" if pressed else "mouse_up"
        self._append({"t": self._elapsed(), "kind": kind, "x": int(x), "y": int(y), "button": btn})

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        self._append(
            {
                "t": self._elapsed(),
                "kind": "mouse_scroll",
                "x": int(x),
                "y": int(y),
                "dx": int(dx),
                "dy": int(dy),
            }
        )

    def _key_event(self, kind: str, key: object) -> None:
        info = describe_key(key)
        if info is None:
            return
        event: dict[str, Any] = {"t": self._elapsed(), "kind": kind, "key": info["name"]}
        # Código/char gravados para reproduzir qualquer tecla (Ctrl, Alt, ç, ; ...).
        if "vk" in info:
            event["vk"] = info["vk"]
        if "char" in info:
            event["char"] = info["char"]
        self._append(event)

    def _on_key_press(self, key: object) -> None:
        self._key_event("key_down", key)

    def _on_key_release(self, key: object) -> None:
        self._key_event("key_up", key)

    def _notify(self) -> None:
        cb = self._on_change
        if cb is not None:
            cb()
