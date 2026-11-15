"""UiNotifier — entrega atualizações de estado à UI com limite de frequência."""

from __future__ import annotations

import threading
from typing import Callable, Optional


class UiNotifier:
    """
    Threads de trabalho (motor, macro, hooks de input) chamam `signal()`, que só
    arma um Event. Uma thread própria chama `push()` no máximo ~15 vezes por
    segundo, de modo que nenhuma thread de input fica bloqueada pela UI.
    """

    def __init__(self, push: Callable[[], None], min_interval_s: float = 1.0 / 15.0) -> None:
        self._push = push
        self._min_interval_s = float(min_interval_s)
        self._event = threading.Event()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="UiNotifier", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._event.set()
        thread, self._thread = self._thread, None
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.0)

    def signal(self) -> None:
        self._event.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._event.wait()
            if self._stop.is_set():
                return
            self._event.clear()
            try:
                self._push()
            except Exception:
                pass
            # Janela mínima entre dois pushes; sinais nesse meio tempo se acumulam.
            self._stop.wait(self._min_interval_s)
