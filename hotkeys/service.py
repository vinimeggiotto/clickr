"""HotkeyService — atalhos globais por ação, com combinações e captura."""

from __future__ import annotations

import queue
import sys
import threading
from typing import Any, Callable, Optional

from app.log import get_logger
from core.errors import ClickrError
from core.keys import modifier_family
from hotkeys.combo import Combo, make_combo, parse_combo
from hotkeys.keynames import describe_key, format_key  # noqa: F401 (reexport)

log = get_logger()

ACTIONS = ("toggle", "stop_all", "pick_point", "macro_record")
DEFAULT_TOGGLE = "F6"


def resolve_key(name: str) -> Combo:
    """Compatibilidade: valida um nome de hotkey (levanta ValueError)."""
    return parse_combo(name)


class HotkeyService:
    """
    Mantém um combo por ação e chama `on_action(ação)` quando pressionado.

    - Windows: RegisterHotKey (a tecla não vaza para o programa em foco).
    - macOS / Linux: listener pynput.
    - As chamadas a `on_action` saem de uma thread própria, nunca do hook de
      teclado, para que trabalho demorado não trave o input do sistema.
    """

    def __init__(
        self,
        on_action: Callable[[str], None],
        bindings: Optional[dict[str, str]] = None,
    ) -> None:
        self._on_action = on_action
        self._lock = threading.RLock()
        self._bindings: dict[str, Optional[Combo]] = {action: None for action in ACTIONS}
        self._backend: Any = None
        self._started = False
        self._queue: "queue.Queue[Any]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._capture_listener: Any = None
        self._capture_mods: set = set()
        self._on_captured: Optional[Callable[[str], None]] = None
        self.load_bindings(bindings or {"toggle": DEFAULT_TOGGLE})

    # --- Bindings -------------------------------------------------------

    def load_bindings(self, mapping: dict[str, str]) -> dict[str, str]:
        """
        Carrega combos salvos sem falhar: inválidos ou repetidos são descartados
        (o de iniciar/parar volta para F6). Retorna o mapa efetivo.
        """
        with self._lock:
            used: set = set()
            for action in ACTIONS:
                combo: Optional[Combo] = None
                text = (mapping.get(action) or "").strip()
                if text:
                    try:
                        combo = parse_combo(text)
                    except ValueError:
                        log.warning("Atalho salvo inválido para %s: %r", action, text)
                if combo is not None and str(combo) in used:
                    combo = None
                if combo is None and action == "toggle":
                    combo = parse_combo(DEFAULT_TOGGLE)
                    if str(combo) in used:
                        combo = None
                if combo is not None:
                    used.add(str(combo))
                self._bindings[action] = combo
            self._apply_locked()
            return self.bindings()

    def bindings(self) -> dict[str, str]:
        with self._lock:
            return {a: (str(c) if c is not None else "") for a, c in self._bindings.items()}

    def combo(self, action: str) -> Optional[Combo]:
        with self._lock:
            return self._bindings.get(action)

    def set_binding(self, action: str, text: str) -> str:
        """Define (ou limpa, com texto vazio) o combo de uma ação. Retorna o nome canônico."""
        if action not in ACTIONS:
            raise ClickrError("hotkey.unknownAction", f"Ação de atalho desconhecida: {action}")
        cleaned = (text or "").strip()
        combo: Optional[Combo] = None
        if cleaned:
            try:
                combo = parse_combo(cleaned)
            except ValueError:
                raise ClickrError(
                    "hotkey.unsupported", f"Hotkey não suportada: {text}", key=str(text)
                ) from None
        with self._lock:
            if combo is not None:
                for other, existing in self._bindings.items():
                    if other != action and existing is not None and str(existing) == str(combo):
                        raise ClickrError(
                            "hotkey.conflict",
                            f"{combo} já é usado por outra ação",
                            key=str(combo),
                            action=other,
                        )
            self._bindings[action] = combo
            self._apply_locked()
        return str(combo) if combo is not None else ""

    def set_hotkey(self, name: str) -> str:
        """Compatibilidade: define o atalho de iniciar/parar."""
        return self.set_binding("toggle", name)

    @property
    def hotkey(self) -> str:
        return self.bindings()["toggle"]

    def is_pressed(self, action: str) -> bool:
        """True enquanto a tecla principal do combo da ação estiver pressionada."""
        with self._lock:
            combo = self._bindings.get(action)
            backend = self._backend
        if combo is None or backend is None:
            return False
        try:
            return bool(backend.is_pressed(combo))
        except Exception:
            return False

    def _apply_locked(self) -> None:
        if self._backend is None:
            return
        active = {a: c for a, c in self._bindings.items() if c is not None}
        try:
            self._backend.apply(active)
        except Exception:
            log.exception("Falha ao aplicar atalhos")

    # --- Ciclo de vida --------------------------------------------------

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
            self._worker = threading.Thread(
                target=self._dispatch_loop, name="HotkeyDispatch", daemon=True
            )
            self._worker.start()
            self._backend = self._create_backend()
            self._backend.start()
            self._apply_locked()

    def stop(self) -> None:
        with self._lock:
            self._stop_capture_locked()
            backend, self._backend = self._backend, None
            was_started, self._started = self._started, False
        if backend is not None:
            try:
                backend.stop()
            except Exception:
                log.exception("Falha ao parar backend de atalhos")
        if was_started:
            self._queue.put(None)

    def _create_backend(self) -> Any:
        if sys.platform == "win32":
            try:
                from hotkeys.backend_win32 import Win32HotkeyBackend

                return Win32HotkeyBackend(self._enqueue)
            except Exception:
                log.exception("RegisterHotKey indisponível; usando listener pynput")
        from hotkeys.backend_pynput import PynputHotkeyBackend

        return PynputHotkeyBackend(self._enqueue)

    def _enqueue(self, action: str) -> None:
        self._queue.put(("action", action))

    def _dispatch_loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                return
            kind, payload = item
            try:
                if kind == "action":
                    self._on_action(payload)
                elif kind == "captured":
                    callback, text = payload
                    callback(text)
            except Exception:
                log.exception("Falha ao tratar atalho")

    # --- Captura --------------------------------------------------------

    @property
    def recording(self) -> bool:
        with self._lock:
            return self._capture_listener is not None

    def begin_capture(self, on_captured: Callable[[str], None]) -> None:
        """
        Captura o próximo combo pressionado e chama on_captured(texto).
        ESC sozinho cancela (texto vazio). Os atalhos ficam suspensos enquanto isso.
        """
        from pynput import keyboard

        from hotkeys.backend_pynput import key_vk

        with self._lock:
            self._stop_capture_locked()
            self._capture_mods = set()
            self._on_captured = on_captured
            if self._backend is not None:
                self._backend.pause()

            def on_press(key: object) -> None:
                vk = key_vk(key, self._capture_listener)
                if vk is None:
                    return
                family = modifier_family(vk)
                if family is not None:
                    self._capture_mods.add(family)
                    return
                combo = make_combo(set(self._capture_mods), vk)
                text = "" if (combo.key == "ESC" and not combo.mods) else str(combo)
                self._finish_capture(text)

            def on_release(key: object) -> None:
                vk = key_vk(key, self._capture_listener)
                family = modifier_family(vk) if vk is not None else None
                if family is not None:
                    self._capture_mods.discard(family)

            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.daemon = True
            self._capture_listener = listener
            listener.start()

    def _finish_capture(self, text: str) -> None:
        with self._lock:
            callback = self._on_captured
            self._stop_capture_locked()
        if callback is not None:
            if self._started:
                self._queue.put(("captured", (callback, text)))
            else:
                callback(text)

    def cancel_capture(self) -> None:
        with self._lock:
            self._stop_capture_locked()

    def _stop_capture_locked(self) -> None:
        listener, self._capture_listener = self._capture_listener, None
        self._on_captured = None
        self._capture_mods = set()
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
            if self._backend is not None:
                self._backend.resume()
